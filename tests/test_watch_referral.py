from django.test import TestCase
from django.contrib.auth.models import User
from videos.models import Video
from accounts.models import Profile
from referrals.models import ReferralLink, ReferralBonus


class WatchReferralTest(TestCase):
    def setUp(self):
        self.referrer = User.objects.create_user(username='ref', password='pass')
        self.referee = User.objects.create_user(username='refed', password='pass')
        # ReferralLink is auto-created by signal; just fetch it
        self.ref_link = ReferralLink.objects.get(user=self.referrer)
        # attach referral
        self.referee.profile.referred_by = self.referrer
        self.referee.profile.save()
        self.video = Video.objects.create(title='Test', url='http://example.com', reward=1.0, duration_seconds=10)

    def test_watch_creates_bonus_and_credits(self):
        self.client.login(username='refed', password='pass')
        resp = self.client.post(f'/videos/{self.video.id}/complete/')
        self.assertEqual(resp.status_code, 200)
        self.referee.profile.refresh_from_db()
        self.referrer.profile.refresh_from_db()
        # referee should have been credited
        self.assertAlmostEqual(self.referee.profile.balance, 1.0)
        # referrer gets 10% bonus
        self.assertAlmostEqual(self.referrer.profile.balance, 0.1)
        # ReferralBonus record exists
        bonuses = ReferralBonus.objects.filter(to_user=self.referrer, from_user=self.referee)
        self.assertTrue(bonuses.exists())
