# New Features Added to RealtorAI Connect

## Overview

Your WhatsApp AI Assistant now has THREE major new features:

1. **Property Images** - Upload and display property photos
2. **Push Notifications** - Real-time alerts for new messages
3. **JWT Authentication** - Secure API access

---

## 1. Property Images

### What It Does
- Upload property photos from mobile app
- Store images on server
- Display images in property listings
- Automatic image optimization and thumbnails

### How to Use in Mobile App

#### **Upload Image for Existing Property**

```javascript
const formData = new FormData();
formData.append('image', {
    uri: photoUri,
    type: 'image/jpeg',
    name: 'property.jpg'
});

const response = await fetch(
    `${API_URL}/api/mobile/properties/${propertyId}/upload-image?image_type=main`,
    {
        method: 'POST',
        body: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    }
);

const data = await response.json();
// data.image_url = URL to display image
```

#### **Create Property with Image**

```javascript
const formData = new FormData();
formData.append('agent_id', agentId);
formData.append('title', 'Marina Bay Condo');
formData.append('location', 'Marina Bay');
formData.append('property_type', 'condo');
formData.append('price', '1200000');
formData.append('bedrooms', '3');
formData.append('bathrooms', '2');
formData.append('image', {
    uri: photoUri,
    type: 'image/jpeg',
    name: 'property.jpg'
});

const response = await fetch(
    `${API_URL}/api/mobile/properties/create-with-image`,
    {
        method: 'POST',
        body: formData
    }
);
```

#### **Display Images**

```javascript
// In your property card component
<Image
    source={{uri: `${API_URL}/${property.image_url}`}}
    style={{width: 300, height: 200}}
/>
```

### Image Features
- **Auto-resize**: Images > 1920x1080 are automatically resized
- **Optimization**: JPEG compression for smaller file sizes
- **Thumbnails**: Automatic thumbnail generation
- **Storage**: Files stored in `uploads/properties/`

---

## 2. Push Notifications

### What It Does
- Send notifications when new messages arrive
- Alert agent even when app is closed
- Custom notification sounds and badges

### Setup (One-Time)

#### **For iOS (Firebase)**

1. Create Firebase project at https://console.firebase.com
2. Add iOS app to project
3. Download `GoogleService-Info.plist`
4. Add to your Xcode project
5. Get Server Key from Firebase Console → Project Settings → Cloud Messaging
6. Set environment variable: `FCM_SERVER_KEY=your_server_key`

#### **For Android**

1. Same Firebase project
2. Add Android app
3. Download `google-services.json`
4. Add to your Android project

### How to Use in Mobile App

#### **Register for Notifications**

```javascript
// In your app initialization
import messaging from '@react-native-firebase/messaging';

async function registerForPushNotifications() {
    // Request permission
    const authStatus = await messaging().requestPermission();

    if (authStatus === messaging.AuthorizationStatus.AUTHORIZED) {
        // Get FCM token
        const fcmToken = await messaging().getToken();

        // Register with backend
        await fetch(`${API_URL}/api/mobile/notifications/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                agent_id: agentId,
                device_token: fcmToken,
                platform: Platform.OS // 'ios' or 'android'
            })
        });
    }
}
```

#### **Handle Notifications**

```javascript
// Background notification handler
messaging().setBackgroundMessageHandler(async (remoteMessage) => {
    console.log('Notification received in background', remoteMessage);

    // Navigate to chat screen
    const conversationId = remoteMessage.data.conversation_id;
    navigateTo('Chat', {conversationId});
});

// Foreground notification handler
messaging().onMessage(async (remoteMessage) => {
    // Show in-app notification
    showInAppNotification(remoteMessage.notification.title, remoteMessage.notification.body);
});
```

#### **Unregister on Logout**

```javascript
async function logout() {
    const fcmToken = await messaging().getToken();

    // Unregister from backend
    await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({device_token: fcmToken})
    });
}
```

### Notification Triggers

Notifications are automatically sent when:
- New message from lead
- Appointment reminder (30 min before)
- Follow-up task due
- Lead becomes "hot"

### Test Notifications

```javascript
// Test if setup is working
const response = await fetch(
    `${API_URL}/api/mobile/notifications/test?agent_id=${agentId}`
);
// Should receive test notification on device
```

---

## 3. JWT Authentication

### What It Does
- Secure API endpoints
- Token-based authentication
- Protect agent data
- Session management

### How to Use in Mobile App

#### **Register New Agent**

```javascript
const response = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'agent@example.com',
        password: 'securePassword123',
        full_name: 'John Smith',
        phone_number: '+1234567890'
    })
});

const data = await response.json();
/*
{
    access_token: "eyJhbGciOiJIUzI1...",
    token_type: "bearer",
    agent_id: "uuid-here",
    email: "agent@example.com",
    full_name: "John Smith"
}
*/

// Save token for future requests
await AsyncStorage.setItem('access_token', data.access_token);
await AsyncStorage.setItem('agent_id', data.agent_id);
```

#### **Login**

```javascript
const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'agent@example.com',
        password: 'securePassword123',
        device_token: fcmToken, // Optional, for push notifications
        platform: 'ios'
    })
});

const data = await response.json();

// Save token
await AsyncStorage.setItem('access_token', data.access_token);
```

#### **Make Authenticated Requests**

```javascript
// Get access token
const accessToken = await AsyncStorage.getItem('access_token');

// Add to all API requests
const response = await fetch(`${API_URL}/api/mobile/conversations`, {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
```

#### **Get Current User Info**

```javascript
const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});

const user = await response.json();
/*
{
    agent_id: "...",
    email: "agent@example.com",
    full_name: "John Smith",
    phone_number: "+1234567890",
    assistant_name: "Alex",
    speaking_style: "professional"
}
*/
```

#### **Handle Token Expiration**

```javascript
// Wrap API calls with error handling
async function apiCall(url, options = {}) {
    const accessToken = await AsyncStorage.getItem('access_token');

    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${accessToken}`
        }
    });

    if (response.status === 401) {
        // Token expired, redirect to login
        navigateToLogin();
        return null;
    }

    return await response.json();
}
```

#### **Logout**

```javascript
const accessToken = await AsyncStorage.getItem('access_token');

await fetch(`${API_URL}/api/auth/logout`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        device_token: fcmToken
    })
});

// Clear local storage
await AsyncStorage.multiRemove(['access_token', 'agent_id']);

// Navigate to login
navigateToLogin();
```

### Demo Account

For testing, use:
- **Email**: `demo@example.com`
- **Password**: `demo123`

---

## Updated API Endpoints

### Authentication Endpoints

```
POST /api/auth/register - Register new agent
POST /api/auth/login - Login with email/password
GET /api/auth/me - Get current user info
POST /api/auth/logout - Logout and unregister device
POST /api/auth/device-token - Register push notification token
DELETE /api/auth/device-token - Unregister token
```

### Image Endpoints

```
POST /api/mobile/properties/{id}/upload-image - Upload property image
POST /api/mobile/properties/create-with-image - Create property with image
GET /uploads/properties/{filename} - Get property image
```

### Notification Endpoints

```
POST /api/mobile/notifications/register - Register for push notifications
GET /api/mobile/notifications/test - Send test notification
```

---

## Environment Variables to Add

Update your `.env` and Railway variables:

```bash
# JWT Secret (generate random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Firebase Cloud Messaging (for push notifications)
FCM_SERVER_KEY=your-fcm-server-key-from-firebase-console

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
```

---

## Database Migrations

After deploying, run the new migration:

```bash
railway run bash -c 'psql $DATABASE_URL < migrations/002_add_auth_and_features.sql'
```

This adds:
- `password_hash` column to `agents` table
- `image_url` column to `properties` table
- `device_tokens` table for push notifications

---

## Security Best Practices

### Store Tokens Securely

```javascript
// Use encrypted storage
import * as SecureStore from 'expo-secure-store';

// Store token
await SecureStore.setItemAsync('access_token', token);

// Retrieve token
const token = await SecureStore.getItemAsync('access_token');
```

### Validate Input

All endpoints validate:
- Email format
- Password strength (minimum 8 characters)
- Image file types (JPEG, PNG only)
- Image file size (max 10MB)

### HTTPS Only

Always use HTTPS in production:
```javascript
const API_URL = "https://your-app.railway.app"; // NOT http://
```

---

## Testing Checklist

### Property Images
- [ ] Upload image from camera
- [ ] Upload image from gallery
- [ ] Create property with image
- [ ] View image in property list
- [ ] View full-size image

### Push Notifications
- [ ] Register device token
- [ ] Receive test notification
- [ ] Receive notification when app is closed
- [ ] Tap notification opens correct chat
- [ ] Unregister on logout

### Authentication
- [ ] Register new account
- [ ] Login with email/password
- [ ] Access protected endpoints with token
- [ ] Handle 401 (expired token)
- [ ] Logout clears token

---

## Troubleshooting

### Images Not Uploading

**Check:**
- File size < 10MB
- File type is JPEG or PNG
- `uploads/properties/` directory exists
- Pillow package installed

**Fix:**
```bash
pip install Pillow==10.1.0
mkdir -p uploads/properties
```

### Push Notifications Not Working

**Check:**
- FCM_SERVER_KEY set in environment
- Firebase project configured
- Device token registered
- App has notification permission

**Test:**
```bash
curl "${API_URL}/api/mobile/notifications/test?agent_id=your-agent-id"
```

### Authentication Failing

**Check:**
- JWT_SECRET_KEY set in environment
- Password hash migration ran
- Token not expired (24 hours)

**Reset password:**
```sql
UPDATE agents
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYVXp.wO.6m'
WHERE email = 'your@email.com';
-- Password will be: demo123
```

---

## Next Steps

1. ✅ Deploy to Railway with new features
2. ✅ Run migration `002_add_auth_and_features.sql`
3. ✅ Set environment variables (JWT_SECRET_KEY, FCM_SERVER_KEY)
4. ✅ Update mobile app with authentication flow
5. ✅ Test image upload
6. ✅ Test push notifications
7. ✅ Deploy to App Store / Play Store!

---

**Your RealtorAI Connect app now has enterprise-grade features!** 🚀

- Secure authentication
- Property photos
- Real-time notifications
