import shutil
import tempfile
from datetime import date

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Complaint, Evidence


class EvidencePreviewAccessTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_root)
        self.settings_override.enable()
        self.victim = User.objects.create_user('victim', password='test-password')
        self.other_user = User.objects.create_user('other', password='test-password')
        self.investigator = User.objects.create_user('investigator', password='test-password', is_staff=True)
        self.complaint = Complaint.objects.create(
            victim=self.victim,
            fraud_type='PHISHING',
            description='A phishing message was received.',
            amount_lost=0,
            date_of_incident=date.today(),
        )
        self.evidence = Evidence.objects.create(
            complaint=self.complaint,
            file=SimpleUploadedFile('receipt.pdf', b'%PDF-1.4 evidence', content_type='application/pdf'),
        )

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)
        super().tearDown()

    def test_owner_and_investigator_can_preview_evidence(self):
        url = reverse('preview_evidence', args=[self.evidence.id])

        self.client.login(username='victim', password='test-password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        response.close()

        self.client.login(username='investigator', password='test-password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response.close()

    def test_other_victim_cannot_preview_evidence(self):
        self.client.login(username='other', password='test-password')
        response = self.client.get(reverse('preview_evidence', args=[self.evidence.id]))
        self.assertEqual(response.status_code, 403)
