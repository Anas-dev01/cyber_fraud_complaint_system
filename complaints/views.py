from django.shortcuts import render, redirect, get_object_or_404
from .models import Complaint, Evidence, VictimProfile
from .forms import ComplaintForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import VictimRegistrationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
import hashlib
from django.conf import settings
import os
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages

# Added imports for email threading
from django.core.mail import send_mail
from django.http import FileResponse, Http404
import threading
import mimetypes

def investigator_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            # SECURITY CHECK: Ensure they are actually staff/investigators
            if user is not None and user.is_staff:
                auth_login(request, user)
                return redirect('investigator_dashboard')
            else:
                messages.error(request, "Access Denied: Not an authorized forensic investigator.")
        else:
            messages.error(request, "Invalid investigator credentials.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'investigator_login.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Smart Routing based on role!
            if user.is_staff:
                return redirect('investigator_dashboard')
            else:
                return redirect('victim_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def index(request):
    # Initialize default fallback values
    total_logs = 0
    active_cases = 0

    if request.user.is_authenticated:
        if request.user.is_staff:
            # GLOBAL CONTEXT FOR INVESTIGATORS
            total_logs = Complaint.objects.count()
            # Count cases that are NOT resolved yet (Pending or Investigating)
            active_cases = Complaint.objects.exclude(status='Resolved').count()
        else:
            # PERSONAL CONTEXT FOR THE INDIVIDUAL VICTIM
            total_logs = Complaint.objects.filter(victim=request.user).count()
            active_cases = Complaint.objects.filter(victim=request.user).exclude(status='Resolved').count()

    context = {
        'total_logs': total_logs,
        'active_cases': active_cases,
    }
    # Return your layout template file name (e.g., index.html or home.html)
    return render(request, 'index.html', context)

@login_required(login_url='login')
def report_fraud(request):
    """Logic for submitting a new fraud complaint with encryption and hashing."""
    # SECURITY CHECK: If the user is an investigator (staff), deny access to victim tools
    if request.user.is_staff:
        messages.error(request, "Investigators are not permitted to file fraud reports.")
        return redirect('investigator_dashboard')

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Create the complaint instance but don't save to DB yet
            complaint = form.save(commit=False)
            # Link it to the logged-in user
            complaint.victim = request.user 
            complaint.save() # This triggers the Tracking ID generation & AES encryption

            # Create an evidence record for every selected file.
            for evidence_file in request.FILES.getlist('evidence_files'):
                Evidence.objects.create(complaint=complaint, file=evidence_file)

            messages.success(request, f"Report Submitted! Your Tracking ID is: {complaint.tracking_id}")
            return redirect('home')
    else:
        form = ComplaintForm()
    
    return render(request, 'report_fraud.html', {'form': form})

@login_required(login_url='login')
def track_status(request):
    """Logic for searching a complaint by Tracking ID."""
    # SECURITY CHECK: Investigators should use the Dashboard, not the victim tracking tool
    if request.user.is_staff:
        return redirect('investigator_dashboard')

    query = request.GET.get('tracking_id')
    complaint = None
    
    if query:
        complaint = Complaint.objects.filter(tracking_id__iexact=query).first()
        if not complaint:
            messages.error(request, "No complaint found with that Tracking ID.")
            
    return render(request, 'track_status.html', {'complaint': complaint})

# Create a helper function for the background thread
def send_welcome_email(user_email, username):
    # Make the subject sound like an official portal notification
    subject = 'Registration Confirmed: Case Management Portal'
    
    # Use a professional structure with a clear greeting, purpose, and sign-off
    message = (
        f"Dear {username},\n\n"
        "Thank you for registering with the Fraud Complaint and Tracking System. "
        "Your profile has been successfully provisioned.\n\n"
        "You may now log in to your dashboard to submit reports, "
        "upload digital evidence, and track the real-time status of your active cases.\n\n"
        "If you did not initiate this registration, please disregard this email.\n\n"
        "Best regards,\n"
        "System Administrator\n"
        "Forensic Investigation Unit"
    )
    
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )

def send_status_update_email(user_email, username, tracking_id):
    subject = f'Case Update Notification: {tracking_id}'
    
    message = (
        f"Dear {username},\n\n"
        f"There has been an official update to your filed case (Tracking ID: {tracking_id}).\n\n"
        "Please log in to your secure dashboard at the Case Management Portal to review the latest investigator remarks and status changes.\n\n"
        "Best regards,\n"
        "System Administrator\n"
        "Forensic Investigation Unit"
    )
    
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
    )

def register(request):
    if request.method == 'POST':
        form = VictimRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            VictimProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
            )
            
            # FIRE THE EMAIL NOTIFICATION IN A BACKGROUND THREAD
            # We use threading so the UI doesn't hang waiting for the SMTP server
            email_thread = threading.Thread(
                target=send_welcome_email, 
                args=(user.email, user.username)
            )
            email_thread.start()

            login(request, user) # Automatically log in the victim
            messages.success(request, f"Account created successfully, {user.username}!")
            return redirect('home')
    else:
        form = VictimRegistrationForm()
    return render(request, 'register.html', {'form': form})


@staff_member_required
def investigator_dashboard(request):
    """A centralized dashboard for investigators to manage and review cases."""
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'investigator_dashboard.html', {'complaints': complaints})


@staff_member_required
def case_detail(request, tracking_id):
    """View to see full case details and verify evidence integrity."""
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
    evidence_list = Evidence.objects.filter(complaint=complaint)
    
    # Logic to verify integrity for each file
    verifications = []
    for ev in evidence_list:
        file_path = ev.file.path
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Compare current hash to database hash
            is_valid = (current_hash == ev.file_hash)
            verifications.append({
                'evidence_id': ev.id,
                'file_name': os.path.basename(file_path),
                'content_type': mimetypes.guess_type(ev.file.name)[0] or 'application/octet-stream',
                'can_preview': _can_preview(ev.file.name),
                'is_valid': is_valid,
                'stored_hash': ev.file_hash,
                'current_hash': current_hash
            })
    
    return render(request, 'case_detail.html', {
        'complaint': complaint,
        'verifications': verifications
    })


@staff_member_required
def victim_profile(request, user_id):
    """Show investigators the contact details for a victim account."""
    victim = get_object_or_404(User, id=user_id, is_staff=False)
    profile = get_object_or_404(VictimProfile, user=victim)
    complaints = Complaint.objects.filter(victim=victim).order_by('-created_at')
    return render(request, 'victim_profile.html', {
        'victim': victim,
        'profile': profile,
        'complaints': complaints,
    })

@login_required
def victim_dashboard(request):
    """A private dashboard for the victim to see their own filed reports."""
    # Only fetch reports where the victim is the logged-in user
    my_reports = (
        Complaint.objects.filter(victim=request.user)
        .prefetch_related('evidence')
        .order_by('-created_at')
    )
    return render(request, 'victim_dashboard.html', {'my_reports': my_reports})


def _can_preview(filename):
    """Return whether the browser can safely render this evidence type inline."""
    content_type, _ = mimetypes.guess_type(filename)
    return bool(content_type and (
        content_type.startswith(('image/', 'audio/', 'video/'))
        or content_type == 'application/pdf'
    ))


@login_required(login_url='login')
def preview_evidence(request, evidence_id):
    """Stream evidence only to its victim or an authorized investigator."""
    evidence = get_object_or_404(Evidence.objects.select_related('complaint'), id=evidence_id)
    if not request.user.is_staff and evidence.complaint.victim_id != request.user.id:
        raise PermissionDenied

    if not evidence.file or not os.path.exists(evidence.file.path):
        raise Http404('Evidence file is unavailable.')

    content_type = mimetypes.guess_type(evidence.file.name)[0] or 'application/octet-stream'
    return FileResponse(
        evidence.file.open('rb'),
        as_attachment=not _can_preview(evidence.file.name),
        filename=os.path.basename(evidence.file.name),
        content_type=content_type,
    )


@login_required(login_url='login')
def add_evidence(request, tracking_id):
    """Let a victim add further evidence after investigator feedback."""
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id, victim=request.user)
    if request.user.is_staff:
        raise PermissionDenied

    if request.method != 'POST':
        return redirect('victim_dashboard')
    if complaint.status == 'RESOLVED':
        messages.error(request, 'Evidence cannot be added to a resolved case.')
        return redirect('victim_dashboard')
    if not complaint.investigator_remarks:
        messages.error(request, 'You can add further evidence once the investigator has provided feedback.')
        return redirect('victim_dashboard')

    evidence_files = request.FILES.getlist('evidence_files')
    if not evidence_files:
        messages.error(request, 'Choose at least one evidence file to upload.')
        return redirect('victim_dashboard')

    for evidence_file in evidence_files:
        Evidence.objects.create(complaint=complaint, file=evidence_file)
    messages.success(request, f'{len(evidence_files)} additional evidence file(s) uploaded.')
    return redirect('victim_dashboard')

@staff_member_required
def update_case_status(request, tracking_id):
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, tracking_id=tracking_id)
        
        # FORENSIC GUARD RAIL: Reject adjustments if already closed
        if complaint.status == 'RESOLVED':
            messages.error(request, "Access Denied: Resolved cases are cryptographically locked.")
            return redirect('case_detail', tracking_id=tracking_id)
            
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        
        if new_status in ['PENDING', 'INVESTIGATING', 'RESOLVED']:
            complaint.status = new_status
            complaint.investigator_remarks = remarks
            complaint.save()
            
            # FIRE THE EMAIL NOTIFICATION IN A BACKGROUND THREAD
            # Access the victim's email and username through the foreign key relationship
            if complaint.victim.email:
                email_thread = threading.Thread(
                    target=send_status_update_email, 
                    args=(complaint.victim.email, complaint.victim.username, complaint.tracking_id)
                )
                email_thread.start()
            
            messages.success(request, f"Case {tracking_id} updated successfully.")
            
    return redirect('case_detail', tracking_id=tracking_id)
