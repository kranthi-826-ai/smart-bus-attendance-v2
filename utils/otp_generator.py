import random
import requests
import time
import hashlib

class OTPHandler:
    def __init__(self):
        self.otp_storage = {}
    
    def generate_otp(self, phone, email):
        """Generate 6-digit OTP but ALWAYS return 123456"""
        otp = "123456"  # FIXED OTP FOR TESTING
        otp_hash = hashlib.sha256(f"{otp}{phone}{email}".encode()).hexdigest()
        
        self.otp_storage[otp_hash] = {
            'otp': otp,
            'phone': phone,
            'email': email,
            'timestamp': time.time(),
            'verified': False
        }
        
        print(f"🎯 TEST OTP: {otp} for {phone}")
        print("🎯 ALWAYS USE OTP: 123456")
        
        return otp, otp_hash
    
    def send_otp_sms(self, phone, otp):
        """BYPASS - No real SMS needed"""
        print(f"📱 TEST MODE - OTP for {phone}: {otp}")
        return True
    
    def send_otp_email(self, email, otp):
        """BYPASS - No real email needed"""
        print(f"📧 TEST MODE - OTP for {email}: {otp}")
        return True
    
    def verify_otp(self, otp_hash, entered_otp):
        """Verify OTP - ALWAYS ACCEPT 123456"""
        print(f"🔍 Verifying OTP: {entered_otp}")
        
        if otp_hash not in self.otp_storage:
            return False, "Invalid OTP session"
        
        otp_data = self.otp_storage[otp_hash]
        
        # Check expiry (10 minutes)
        if time.time() - otp_data['timestamp'] > 600:
            del self.otp_storage[otp_hash]
            return False, "OTP expired"
        
        # ALWAYS ACCEPT 123456
        if entered_otp == "123456":
            otp_data['verified'] = True
            print("✅ OTP VERIFIED SUCCESSFULLY!")
            return True, "OTP verified successfully"
        else:
            print(f"❌ Wrong OTP. Use: 123456")
            return False, "Invalid OTP - Use 123456 for testing"
    
    def get_verified_data(self, otp_hash):
        """Get verified OTP data"""
        if (otp_hash in self.otp_storage and 
            self.otp_storage[otp_hash]['verified']):
            data = self.otp_storage[otp_hash]
            del self.otp_storage[otp_hash]
            return data
        return None