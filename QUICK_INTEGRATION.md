# Quick Integration - Copy & Paste These Into Your App

## 1. API Client (Copy this entire file)

```javascript
// services/api.js
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://your-app-name.up.railway.app';

class API {
  async request(endpoint, options = {}) {
    const token = await AsyncStorage.getItem('access_token');

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        await AsyncStorage.removeItem('access_token');
        throw new Error('Session expired. Please login again.');
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Login
  login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  // Get conversations
  getConversations(agentId) {
    return this.request(`/api/mobile/conversations?agent_id=${agentId}`);
  }

  // Get messages
  getMessages(conversationId) {
    return this.request(`/api/mobile/conversations/${conversationId}/messages`);
  }

  // Send message
  sendMessage(userId, userName, message, agentId) {
    return this.request('/api/mobile/chat/send', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        user_name: userName,
        message,
        agent_id: agentId,
      }),
    });
  }

  // Search properties
  searchProperties(params) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/api/mobile/properties/search?${query}`);
  }

  // Upload property image
  async uploadPropertyImage(propertyId, imageUri) {
    const token = await AsyncStorage.getItem('access_token');

    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'property.jpg',
    });

    const response = await fetch(
      `${API_BASE_URL}/api/mobile/properties/${propertyId}/upload-image`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      }
    );

    return await response.json();
  }

  // Register push notification token
  registerNotificationToken(agentId, deviceToken, platform) {
    return this.request('/api/mobile/notifications/register', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: agentId,
        device_token: deviceToken,
        platform,
      }),
    });
  }
}

export default new API();
```

---

## 2. Login Screen (Copy this)

```javascript
// screens/LoginScreen.js
import React, { useState } from 'react';
import { View, TextInput, Button, Alert, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const response = await api.login(email, password);

      await AsyncStorage.setItem('access_token', response.access_token);
      await AsyncStorage.setItem('agent_id', response.agent_id);

      navigation.replace('Main');
    } catch (error) {
      Alert.alert('Login Failed', error.message);
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
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button title="Login" onPress={handleLogin} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, justifyContent: 'center' },
  input: { borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
});
```

---

## 3. Chat Screen (Copy this)

```javascript
// screens/ChatScreen.js
import React, { useEffect, useState } from 'react';
import { View, FlatList, TextInput, Button, Text, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function ChatScreen({ route }) {
  const { conversationId, contactName } = route.params;
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    loadMessages();
    const interval = setInterval(loadMessages, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMessages = async () => {
    const data = await api.getMessages(conversationId);
    setMessages(data);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const agentId = await AsyncStorage.getItem('agent_id');
    const response = await api.sendMessage(
      conversationId,
      contactName,
      input,
      agentId
    );

    setInput('');
    loadMessages(); // Refresh messages
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        renderItem={({ item }) => (
          <View style={item.sender_type === 'USER' ? styles.userMsg : styles.aiMsg}>
            <Text>{item.message_text}</Text>
          </View>
        )}
        keyExtractor={(item, i) => i.toString()}
        inverted
      />
      <View style={styles.inputBox}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Type a message..."
        />
        <Button title="Send" onPress={sendMessage} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  userMsg: { alignSelf: 'flex-end', backgroundColor: '#DCF8C6', padding: 10, margin: 5, borderRadius: 10 },
  aiMsg: { alignSelf: 'flex-start', backgroundColor: '#FFF', padding: 10, margin: 5, borderRadius: 10 },
  inputBox: { flexDirection: 'row', padding: 10 },
  input: { flex: 1, borderWidth: 1, padding: 10, marginRight: 10, borderRadius: 5 },
});
```

---

## 4. Conversations List (Copy this)

```javascript
// screens/ConversationsScreen.js
import React, { useEffect, useState } from 'react';
import { FlatList, TouchableOpacity, Text, View, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';

export default function ConversationsScreen({ navigation }) {
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    const agentId = await AsyncStorage.getItem('agent_id');
    const data = await api.getConversations(agentId);
    setConversations(data);
  };

  return (
    <FlatList
      data={conversations}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.item}
          onPress={() => navigation.navigate('Chat', {
            conversationId: item.conversation_id,
            contactName: item.contact_name,
          })}
        >
          <Text style={styles.name}>{item.contact_name}</Text>
          <Text style={styles.message}>{item.last_message}</Text>
          {item.unread_count > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{item.unread_count}</Text>
            </View>
          )}
        </TouchableOpacity>
      )}
      keyExtractor={(item) => item.conversation_id}
      refreshing={false}
      onRefresh={loadConversations}
    />
  );
}

const styles = StyleSheet.create({
  item: { padding: 15, borderBottomWidth: 1, borderColor: '#eee' },
  name: { fontSize: 16, fontWeight: 'bold' },
  message: { fontSize: 14, color: '#666', marginTop: 5 },
  badge: { position: 'absolute', right: 15, top: 15, backgroundColor: 'green', borderRadius: 10, padding: 5 },
  badgeText: { color: 'white', fontSize: 12 },
});
```

---

## 5. Deploy & Update URL

### **Step 1: Deploy to Railway**

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant

railway init
railway add  # PostgreSQL
railway add  # Redis
railway up

# Get URL
railway domain
```

### **Step 2: Update API URL in Your App**

In `services/api.js`, change:

```javascript
const API_BASE_URL = 'https://your-actual-app-name.up.railway.app';
```

### **Step 3: Test**

Login with:
- **Email**: demo@example.com
- **Password**: demo123

---

## 6. Complete Flow

```
1. User opens app
   ↓
2. LoginScreen → api.login()
   ↓
3. Save token to AsyncStorage
   ↓
4. Navigate to ConversationsScreen
   ↓
5. Load conversations → api.getConversations()
   ↓
6. Tap conversation → Navigate to ChatScreen
   ↓
7. Load messages → api.getMessages()
   ↓
8. Send message → api.sendMessage()
   ↓
9. Get AI response automatically
   ↓
10. Display in chat
```

---

## Demo Credentials

**Email**: demo@example.com
**Password**: demo123

Use these to test your integration!

---

**Copy these files into your app and you're done!** 🚀

Just remember to:
1. Deploy backend to Railway
2. Update `API_BASE_URL`
3. Test login with demo credentials
