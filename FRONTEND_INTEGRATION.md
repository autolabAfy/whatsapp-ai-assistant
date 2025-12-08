# Frontend Integration Guide - RealtorAI Connect

## Overview

This guide shows you exactly how to connect your RealtorAI Connect mobile app to the backend.

---

## Step 1: Deploy Backend First (Required)

Before integrating, deploy your backend to get a permanent URL:

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant

# Deploy to Railway
railway init
railway add  # PostgreSQL
railway add  # Redis
railway open  # Set environment variables
railway up   # Deploy!

# Get your URL
railway domain
```

You'll get: `https://whatsapp-ai-assistant-production.up.railway.app`

**Save this URL - you'll use it in your mobile app!**

---

## Step 2: Configure API Base URL in Your App

### **Option A: If You Built with React Native / Expo**

Create an API configuration file:

```javascript
// config/api.js
const API_CONFIG = {
  // Development (local testing)
  development: 'http://localhost:8000',

  // Production (Railway deployment)
  production: 'https://your-app-name.up.railway.app',

  // Use production for now
  baseURL: 'https://your-app-name.up.railway.app'
};

export default API_CONFIG;
```

### **Option B: If You Built with Google AI Studio / AppSheet**

In your app settings, add:
- **API Base URL**: `https://your-app-name.up.railway.app`
- **Environment**: `production`

### **Option C: Environment Variables**

```javascript
// .env (in your mobile app)
API_URL=https://your-app-name.up.railway.app
API_TIMEOUT=30000
```

```javascript
// In your app code
import { API_URL } from '@env';

const baseURL = API_URL || 'https://your-app-name.up.railway.app';
```

---

## Step 3: Create API Client

### **Option 1: Using Fetch API (Simple)**

```javascript
// services/api.js
const API_BASE_URL = 'https://your-app-name.up.railway.app';

class APIClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = null;
  }

  // Set authentication token
  setToken(token) {
    this.token = token;
  }

  // Make authenticated request
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        timeout: 30000,
      });

      // Handle 401 - token expired
      if (response.status === 401) {
        // Clear token and redirect to login
        this.token = null;
        // Navigate to login screen
        throw new Error('Authentication required');
      }

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // GET request
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;

    return this.request(url, { method: 'GET' });
  }

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Upload file (for property images)
  async uploadFile(endpoint, file, additionalData = {}) {
    const formData = new FormData();
    formData.append('image', file);

    Object.keys(additionalData).forEach(key => {
      formData.append(key, additionalData[key]);
    });

    const url = `${this.baseURL}${endpoint}`;
    const headers = {};

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    return await response.json();
  }
}

// Export singleton instance
export default new APIClient();
```

### **Option 2: Using Axios (Recommended)**

```bash
# Install axios
npm install axios
# or
yarn add axios
```

```javascript
// services/api.js
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://your-app-name.up.railway.app';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired - clear and redirect to login
      await AsyncStorage.removeItem('access_token');
      // Navigate to login
      // NavigationService.navigate('Login');
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## Step 4: Implement Authentication

### **Login Screen Integration**

```javascript
// screens/LoginScreen.js
import React, { useState } from 'react';
import { View, TextInput, Button, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);

    try {
      const response = await api.post('/api/auth/login', {
        email,
        password,
      });

      // Save token
      await AsyncStorage.setItem('access_token', response.data.access_token);
      await AsyncStorage.setItem('agent_id', response.data.agent_id);
      await AsyncStorage.setItem('user_name', response.data.full_name);

      // Navigate to main app
      navigation.replace('Main');

    } catch (error) {
      Alert.alert('Login Failed', error.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View>
      <TextInput
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button
        title={loading ? "Logging in..." : "Login"}
        onPress={handleLogin}
        disabled={loading}
      />
    </View>
  );
}
```

### **Auto-Login on App Start**

```javascript
// App.js or navigation/index.js
import React, { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingScreen />;
  }

  return isAuthenticated ? <MainApp /> : <LoginScreen />;
}
```

---

## Step 5: Integrate Chat Features

### **Chats Screen - Load Conversations**

```javascript
// screens/ChatsScreen.js
import React, { useEffect, useState } from 'react';
import { FlatList, TouchableOpacity, Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function ChatsScreen({ navigation }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();

    // Refresh every 30 seconds
    const interval = setInterval(loadConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    try {
      const agentId = await AsyncStorage.getItem('agent_id');

      const response = await api.get('/api/mobile/conversations', {
        agent_id: agentId,
        limit: 50
      });

      setConversations(response.data);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderConversation = ({ item }) => (
    <TouchableOpacity
      onPress={() => navigation.navigate('Chat', {
        conversationId: item.conversation_id,
        contactName: item.contact_name
      })}
    >
      <View style={styles.conversationItem}>
        <Text style={styles.contactName}>{item.contact_name}</Text>
        <Text style={styles.lastMessage}>{item.last_message}</Text>
        <Text style={styles.time}>{formatTime(item.last_message_time)}</Text>
        {item.unread_count > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{item.unread_count}</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <FlatList
      data={conversations}
      renderItem={renderConversation}
      keyExtractor={(item) => item.conversation_id}
      refreshing={loading}
      onRefresh={loadConversations}
    />
  );
}
```

### **Chat Screen - Send Messages**

```javascript
// screens/ChatScreen.js
import React, { useEffect, useState } from 'react';
import { FlatList, TextInput, Button } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function ChatScreen({ route }) {
  const { conversationId, contactName } = route.params;
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadMessages();

    // Auto-refresh every 5 seconds
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, [conversationId]);

  const loadMessages = async () => {
    try {
      const response = await api.get(
        `/api/mobile/conversations/${conversationId}/messages`
      );

      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    setSending(true);
    const messageText = inputText;
    setInputText(''); // Clear input immediately

    try {
      const agentId = await AsyncStorage.getItem('agent_id');

      const response = await api.post('/api/mobile/chat/send', {
        user_id: conversationId, // Or phone number
        user_name: contactName,
        message: messageText,
        agent_id: agentId
      });

      // Add user message and AI response to local state
      setMessages(prev => [...prev,
        {
          sender_type: 'USER',
          message_text: messageText,
          timestamp: new Date().toISOString()
        },
        {
          sender_type: 'AI',
          message_text: response.data.ai_response,
          timestamp: new Date().toISOString()
        }
      ]);

      // Show recommended properties if any
      if (response.data.properties) {
        showPropertyRecommendations(response.data.properties);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      Alert.alert('Error', 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const renderMessage = ({ item }) => (
    <View style={item.sender_type === 'USER' ? styles.userMessage : styles.aiMessage}>
      <Text>{item.message_text}</Text>
      <Text style={styles.timestamp}>{formatTime(item.timestamp)}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item, index) => index.toString()}
        inverted
      />
      <View style={styles.inputContainer}>
        <TextInput
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message..."
          style={styles.input}
        />
        <Button
          title="Send"
          onPress={sendMessage}
          disabled={sending || !inputText.trim()}
        />
      </View>
    </View>
  );
}
```

---

## Step 6: Property Images Integration

### **Upload Property Image**

```javascript
// screens/AddPropertyScreen.js
import React, { useState } from 'react';
import * as ImagePicker from 'expo-image-picker';
import api from '../services/api';

export default function AddPropertyScreen() {
  const [image, setImage] = useState(null);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [16, 9],
      quality: 0.8,
    });

    if (!result.canceled) {
      setImage(result.assets[0]);
    }
  };

  const createProperty = async () => {
    try {
      const agentId = await AsyncStorage.getItem('agent_id');

      const formData = new FormData();
      formData.append('agent_id', agentId);
      formData.append('title', propertyTitle);
      formData.append('location', location);
      formData.append('property_type', propertyType);
      formData.append('price', price);
      formData.append('bedrooms', bedrooms);
      formData.append('bathrooms', bathrooms);

      if (image) {
        formData.append('image', {
          uri: image.uri,
          type: 'image/jpeg',
          name: 'property.jpg',
        });
      }

      const response = await api.uploadFile(
        '/api/mobile/properties/create-with-image',
        formData
      );

      Alert.alert('Success', 'Property created!');
      navigation.goBack();

    } catch (error) {
      Alert.alert('Error', 'Failed to create property');
    }
  };

  return (
    <View>
      {image && <Image source={{ uri: image.uri }} style={styles.preview} />}
      <Button title="Pick Image" onPress={pickImage} />
      {/* Other property fields */}
      <Button title="Create Property" onPress={createProperty} />
    </View>
  );
}
```

---

## Step 7: Push Notifications Integration

### **Setup Firebase (One-Time)**

```bash
# Install Firebase
npm install @react-native-firebase/app @react-native-firebase/messaging
```

### **Register for Notifications**

```javascript
// services/notifications.js
import messaging from '@react-native-firebase/messaging';
import api from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export async function requestNotificationPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    await registerDeviceToken();
  }
}

async function registerDeviceToken() {
  try {
    const token = await messaging().getToken();
    const agentId = await AsyncStorage.getItem('agent_id');

    await api.post('/api/mobile/notifications/register', {
      agent_id: agentId,
      device_token: token,
      platform: Platform.OS,
    });

    console.log('Device token registered');
  } catch (error) {
    console.error('Failed to register device token:', error);
  }
}

// Handle background notifications
messaging().setBackgroundMessageHandler(async (remoteMessage) => {
  console.log('Notification received in background', remoteMessage);
});

// Handle foreground notifications
export function onMessageReceived(callback) {
  return messaging().onMessage(async (remoteMessage) => {
    callback(remoteMessage);
  });
}
```

### **Use in App**

```javascript
// App.js
import { requestNotificationPermission, onMessageReceived } from './services/notifications';

useEffect(() => {
  // Request permission on app start
  requestNotificationPermission();

  // Listen for notifications
  const unsubscribe = onMessageReceived((notification) => {
    // Show in-app notification or update UI
    console.log('New notification:', notification);

    // Refresh conversations list
    if (notification.data.type === 'new_message') {
      refreshConversations();
    }
  });

  return unsubscribe;
}, []);
```

---

## Step 8: Complete Integration Checklist

### **✅ Before Deployment**
- [ ] Replace `API_BASE_URL` with your Railway URL
- [ ] Test login/register flow
- [ ] Test chat functionality
- [ ] Test image upload
- [ ] Setup Firebase project
- [ ] Add environment variables

### **✅ After Deployment**
- [ ] Test with production API
- [ ] Verify push notifications work
- [ ] Test image display
- [ ] Check authentication persistence
- [ ] Monitor API errors

---

## Quick Start Code

Copy this into your project:

```javascript
// config/api.js
export const API_BASE_URL = 'https://your-app.railway.app';

// services/api.js
// [Use the APIClient code from Step 3]

// App.js
import api from './services/api';

// Set base URL
api.defaults.baseURL = API_BASE_URL;

// Now use throughout your app!
```

---

**Your frontend is now ready to connect to the backend!** 🚀

Next: Deploy backend to Railway and update `API_BASE_URL` with your production URL.
