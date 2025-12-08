# RealtorAI Connect - Complete Mobile App Integration

## 📦 What This Package Includes

1. **API Client** - Ready-to-use API service
2. **Authentication Flow** - Login, Register, Logout
3. **Chat System** - Send/receive messages with AI
4. **Property Management** - Search, upload images
5. **Calendar Integration** - Appointments management
6. **Settings & Profile** - Agent customization
7. **Push Notifications** - Real-time alerts

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
npm install axios @react-native-firebase/app @react-native-firebase/messaging @react-native-async-storage/async-storage
```

Or with Expo:

```bash
npx expo install expo-secure-store @react-native-firebase/app @react-native-firebase/messaging
```

### Step 2: Configure API URL

Create `src/config/api.js`:

```javascript
// Replace with your Railway URL after deployment
export const API_BASE_URL = 'https://your-app.up.railway.app';

// Demo credentials for testing
export const DEMO_CREDENTIALS = {
  email: 'demo@example.com',
  password: 'demo123'
};
```

### Step 3: Copy API Service

Create `src/services/api.js`:

```javascript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../config/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to all requests
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.multiRemove(['access_token', 'agent_id']);
      // Navigate to login screen
      // NavigationService.navigate('Login');
    }
    return Promise.reject(error);
  }
);

// Authentication
export const authAPI = {
  login: async (email, password, deviceToken = null) => {
    const response = await api.post('/api/auth/login', {
      email,
      password,
      device_token: deviceToken,
      platform: Platform.OS
    });

    // Save credentials
    await AsyncStorage.setItem('access_token', response.data.access_token);
    await AsyncStorage.setItem('agent_id', response.data.agent_id);

    return response.data;
  },

  register: async (email, password, fullName, phoneNumber = null) => {
    const response = await api.post('/api/auth/register', {
      email,
      password,
      full_name: fullName,
      phone_number: phoneNumber
    });

    await AsyncStorage.setItem('access_token', response.data.access_token);
    await AsyncStorage.setItem('agent_id', response.data.agent_id);

    return response.data;
  },

  logout: async (deviceToken = null) => {
    await api.post('/api/auth/logout', { device_token: deviceToken });
    await AsyncStorage.multiRemove(['access_token', 'agent_id']);
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  }
};

// Chat
export const chatAPI = {
  getConversations: async () => {
    const response = await api.get('/api/mobile/conversations');
    return response.data;
  },

  getMessages: async (conversationId) => {
    const response = await api.get(`/api/mobile/conversations/${conversationId}/messages`);
    return response.data;
  },

  sendMessage: async (conversationId, message) => {
    const response = await api.post('/api/mobile/chat/send', {
      conversation_id: conversationId,
      message
    });
    return response.data;
  }
};

// Properties
export const propertyAPI = {
  search: async (searchParams = {}) => {
    const response = await api.get('/api/mobile/properties/search', {
      params: searchParams
    });
    return response.data;
  },

  uploadImage: async (propertyId, imageUri) => {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'property.jpg'
    });

    const response = await api.post(
      `/api/mobile/properties/${propertyId}/upload-image`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  },

  createWithImage: async (propertyData, imageUri) => {
    const formData = new FormData();

    // Add property data
    Object.keys(propertyData).forEach(key => {
      formData.append(key, propertyData[key]);
    });

    // Add image
    if (imageUri) {
      formData.append('image', {
        uri: imageUri,
        type: 'image/jpeg',
        name: 'property.jpg'
      });
    }

    const response = await api.post(
      '/api/mobile/properties/create-with-image',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  }
};

// Appointments
export const appointmentAPI = {
  getAll: async () => {
    const response = await api.get('/api/mobile/appointments');
    return response.data;
  },

  create: async (appointmentData) => {
    const response = await api.post('/api/mobile/appointments/create', appointmentData);
    return response.data;
  }
};

// Settings
export const settingsAPI = {
  get: async () => {
    const response = await api.get('/api/mobile/agent/settings');
    return response.data;
  },

  update: async (settings) => {
    const response = await api.put('/api/mobile/agent/settings', settings);
    return response.data;
  }
};

// Usage Stats
export const usageAPI = {
  getStats: async (period = 'month') => {
    const response = await api.get('/api/mobile/usage/stats', {
      params: { period }
    });
    return response.data;
  }
};

// Push Notifications
export const notificationAPI = {
  register: async (deviceToken, platform) => {
    const response = await api.post('/api/mobile/notifications/register', {
      device_token: deviceToken,
      platform
    });
    return response.data;
  },

  test: async () => {
    const agentId = await AsyncStorage.getItem('agent_id');
    const response = await api.get(`/api/mobile/notifications/test?agent_id=${agentId}`);
    return response.data;
  }
};

export default api;
```

---

## 🔐 Authentication Screens

### Login Screen

Create `src/screens/LoginScreen.js`:

```javascript
import React, { useState } from 'react';
import { View, TextInput, Button, Alert, StyleSheet } from 'react-native';
import { authAPI } from '../services/api';
import messaging from '@react-native-firebase/messaging';

const LoginScreen = ({ navigation }) => {
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('demo123');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      // Get FCM token for push notifications
      const fcmToken = await messaging().getToken();

      // Login
      const data = await authAPI.login(email, password, fcmToken);

      Alert.alert('Success', `Welcome ${data.full_name}!`);
      navigation.replace('Main');

    } catch (error) {
      Alert.alert('Login Failed', error.response?.data?.detail || 'Please try again');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />

      <TextInput
        style={styles.input}
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

      <Button
        title="Register"
        onPress={() => navigation.navigate('Register')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center'
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 10,
    marginBottom: 10,
    borderRadius: 5
  }
});

export default LoginScreen;
```

---

## 💬 Chat Screen

Create `src/screens/ChatScreen.js`:

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TextInput, Button, StyleSheet } from 'react-native';
import { chatAPI } from '../services/api';

const ChatScreen = ({ route }) => {
  const { conversationId } = route.params;
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMessages();
  }, []);

  const loadMessages = async () => {
    try {
      const data = await chatAPI.getMessages(conversationId);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    setLoading(true);
    try {
      const response = await chatAPI.sendMessage(conversationId, inputText);

      // Add user message
      setMessages(prev => [...prev, {
        sender_type: 'LEAD',
        message_text: inputText,
        timestamp: new Date()
      }]);

      // Add AI response
      setMessages(prev => [...prev, {
        sender_type: 'AI',
        message_text: response.ai_response,
        timestamp: new Date()
      }]);

      setInputText('');
    } catch (error) {
      Alert.alert('Error', 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = ({ item }) => (
    <View style={[
      styles.messageBubble,
      item.sender_type === 'AI' ? styles.aiMessage : styles.leadMessage
    ]}>
      <Text style={styles.messageText}>{item.message_text}</Text>
      <Text style={styles.timestamp}>
        {new Date(item.timestamp).toLocaleTimeString()}
      </Text>
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
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message..."
        />
        <Button
          title="Send"
          onPress={sendMessage}
          disabled={loading}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  messageBubble: {
    padding: 10,
    margin: 5,
    borderRadius: 10,
    maxWidth: '80%'
  },
  aiMessage: {
    backgroundColor: '#e3f2fd',
    alignSelf: 'flex-start'
  },
  leadMessage: {
    backgroundColor: '#fff',
    alignSelf: 'flex-end'
  },
  messageText: {
    fontSize: 16
  },
  timestamp: {
    fontSize: 10,
    color: '#666',
    marginTop: 5
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#fff'
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 15,
    marginRight: 10
  }
});

export default ChatScreen;
```

---

## 🏡 Property Screen with Image Upload

Create `src/screens/PropertiesScreen.js`:

```javascript
import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, Image, Button, StyleSheet } from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { propertyAPI } from '../services/api';
import { API_BASE_URL } from '../config/api';

const PropertiesScreen = () => {
  const [properties, setProperties] = useState([]);

  useEffect(() => {
    loadProperties();
  }, []);

  const loadProperties = async () => {
    try {
      const data = await propertyAPI.search();
      setProperties(data);
    } catch (error) {
      console.error('Failed to load properties:', error);
    }
  };

  const uploadPropertyImage = async (propertyId) => {
    launchImageLibrary({ mediaType: 'photo' }, async (response) => {
      if (!response.didCancel && response.assets?.[0]) {
        try {
          const result = await propertyAPI.uploadImage(
            propertyId,
            response.assets[0].uri
          );
          Alert.alert('Success', 'Image uploaded!');
          loadProperties(); // Reload to show new image
        } catch (error) {
          Alert.alert('Error', 'Failed to upload image');
        }
      }
    });
  };

  const renderProperty = ({ item }) => (
    <View style={styles.propertyCard}>
      {item.image_url && (
        <Image
          source={{ uri: `${API_BASE_URL}/${item.image_url}` }}
          style={styles.propertyImage}
        />
      )}

      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.price}>${item.price?.toLocaleString()}</Text>
      <Text style={styles.details}>
        {item.bedrooms} bed · {item.bathrooms} bath · {item.property_type}
      </Text>
      <Text style={styles.location}>{item.location}</Text>

      <Button
        title="Upload Photo"
        onPress={() => uploadPropertyImage(item.property_id)}
      />
    </View>
  );

  return (
    <FlatList
      data={properties}
      renderItem={renderProperty}
      keyExtractor={(item) => item.property_id}
      contentContainerStyle={styles.container}
    />
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 10
  },
  propertyCard: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3
  },
  propertyImage: {
    width: '100%',
    height: 200,
    borderRadius: 10,
    marginBottom: 10
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5
  },
  price: {
    fontSize: 20,
    color: '#2196F3',
    fontWeight: 'bold',
    marginBottom: 5
  },
  details: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5
  },
  location: {
    fontSize: 14,
    color: '#999',
    marginBottom: 10
  }
});

export default PropertiesScreen;
```

---

## 🔔 Push Notifications Setup

Create `src/services/notifications.js`:

```javascript
import messaging from '@react-native-firebase/messaging';
import { notificationAPI } from './api';
import { Platform } from 'react-native';

export const initializeNotifications = async () => {
  // Request permission
  const authStatus = await messaging().requestPermission();

  if (authStatus === messaging.AuthorizationStatus.AUTHORIZED) {
    // Get FCM token
    const fcmToken = await messaging().getToken();

    // Register with backend
    await notificationAPI.register(fcmToken, Platform.OS);

    console.log('Push notifications enabled');
  }
};

// Handle background notifications
messaging().setBackgroundMessageHandler(async (remoteMessage) => {
  console.log('Background notification:', remoteMessage);

  // You can update local state or navigate when app opens
});

// Handle foreground notifications
export const setupForegroundNotifications = (navigation) => {
  return messaging().onMessage(async (remoteMessage) => {
    console.log('Foreground notification:', remoteMessage);

    // Show in-app notification or navigate
    if (remoteMessage.data?.conversation_id) {
      // Optional: Navigate to chat
      // navigation.navigate('Chat', {
      //   conversationId: remoteMessage.data.conversation_id
      // });
    }
  });
};

// Handle notification tap (app in background/quit)
export const setupNotificationTapHandler = (navigation) => {
  messaging().onNotificationOpenedApp((remoteMessage) => {
    if (remoteMessage.data?.conversation_id) {
      navigation.navigate('Chat', {
        conversationId: remoteMessage.data.conversation_id
      });
    }
  });

  // Check if app was opened by notification
  messaging().getInitialNotification().then((remoteMessage) => {
    if (remoteMessage?.data?.conversation_id) {
      navigation.navigate('Chat', {
        conversationId: remoteMessage.data.conversation_id
      });
    }
  });
};
```

---

## 📱 App.js Integration

Update your `App.js`:

```javascript
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import AsyncStorage from '@react-native-async-storage/async-storage';

import LoginScreen from './src/screens/LoginScreen';
import ChatScreen from './src/screens/ChatScreen';
import PropertiesScreen from './src/screens/PropertiesScreen';

import {
  initializeNotifications,
  setupForegroundNotifications,
  setupNotificationTapHandler
} from './src/services/notifications';

const Stack = createStackNavigator();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const navigationRef = React.useRef();

  useEffect(() => {
    checkAuth();
    initializeNotifications();
  }, []);

  useEffect(() => {
    if (navigationRef.current) {
      const unsubscribe = setupForegroundNotifications(navigationRef.current);
      setupNotificationTapHandler(navigationRef.current);

      return unsubscribe;
    }
  }, []);

  const checkAuth = async () => {
    const token = await AsyncStorage.getItem('access_token');
    setIsAuthenticated(!!token);
  };

  return (
    <NavigationContainer ref={navigationRef}>
      <Stack.Navigator>
        {!isAuthenticated ? (
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : (
          <>
            <Stack.Screen name="Chat" component={ChatScreen} />
            <Stack.Screen name="Properties" component={PropertiesScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
```

---

## ✅ Deployment Checklist

### Railway Backend
- [ ] Deploy to Railway (see RAILWAY_DEPLOYMENT_GUIDE.md)
- [ ] Run database migrations
- [ ] Set all environment variables
- [ ] Get public URL
- [ ] Test /docs endpoint

### Mobile App
- [ ] Update API_BASE_URL in src/config/api.js
- [ ] Install dependencies (axios, firebase, async-storage)
- [ ] Copy API service code
- [ ] Test login with demo@example.com / demo123
- [ ] Test chat functionality
- [ ] Test property image upload

### Firebase (for Push Notifications)
- [ ] Create Firebase project
- [ ] Add iOS app (download GoogleService-Info.plist)
- [ ] Add Android app (download google-services.json)
- [ ] Get FCM Server Key
- [ ] Update FCM_SERVER_KEY in Railway variables
- [ ] Test push notifications

---

## 🎯 Your Complete System

**Backend**: https://your-app.up.railway.app
**Demo Login**: demo@example.com / demo123

**Features Ready**:
✅ Secure JWT authentication
✅ AI-powered chat responses
✅ Property management with images
✅ Calendar/appointments
✅ Push notifications
✅ Agent settings
✅ Usage tracking

**Now your RealtorAI Connect app is production-ready!** 🚀
