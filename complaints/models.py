from django.db import models
from django.contrib.auth.models import User
import uuid
from utils.integrity import generate_file_hash
from utils.encryption import encrypt_data, decrypt_data

class VictimProfile(models.Model):
    """Contact details that belong to the victim account, not each report."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='victim_profile')
    phone_number = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.phone_number and not self.phone_number.startswith('gAAAA'):
            self.phone_number = encrypt_data(self.phone_number)
        super().save(*args, **kwargs)

    @property
    def decrypted_phone(self):
        return decrypt_data(self.phone_number)

    def __str__(self):
        return f"Profile for {self.user.username}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('FRAUDULENT', 'Marked as False Claim'),
    ]

    FRAUD_TYPES = [
        ('PHISHING', 'Phishing/Email Scam'),
        ('IDENTITY_THEFT', 'Identity Theft'),
        ('FINANCIAL', 'Online Banking Fraud'),
        ('ROMANCE', 'Romance Scam'),
        ('OTHER', 'Other Cybercrime'),
    ]

    # Tracking & Ownership
    tracking_id = models.CharField(max_length=12, unique=True, editable=False)
    victim = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    
    # Incident Details
    fraud_type = models.CharField(max_length=20, choices=FRAUD_TYPES)
    description = models.TextField()
    amount_lost = models.DecimalField('Amount lost (₦)', max_digits=12, decimal_places=2, default=0.00)
    date_of_incident = models.DateField()

    # Investigator Feedback Section
    investigator_remarks = models.TextField(blank=True, null=True)
    
    # Metadata & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            # Generates a unique 8-character ID for tracking
            self.tracking_id = str(uuid.uuid4()).upper()[:8]
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_id} - {self.get_fraud_type_display()}"

class Evidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField(upload_to='evidence/')
    file_hash = models.CharField(max_length=64, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Save the file first so we have a physical path on your Kali drive to hash
        super().save(*args, **kwargs)
        
        # If there is no hash yet, generate it using our utility
        if not self.file_hash:
            self.file_hash = generate_file_hash(self.file.path)
            # Save again to update only the file_hash field in the database
            super().save(update_fields=['file_hash'])

    def __str__(self):
        return f"Evidence for {self.complaint.tracking_id}"
