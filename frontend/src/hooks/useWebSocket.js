import { useEffect, useRef, useState } from 'react';

/**
 * WebSocket Hook
 * Real-time notifications için
 * 
 * Usage:
 *   const { isConnected, lastMessage, sendMessage } = useWebSocket();
 */
export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  
  const connect = () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('No token, skipping WebSocket connection');
        return;
      }
      
      // WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/notifications?token=${token}`;
      
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        
        // Heartbeat (ping-pong)
        const pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send('ping');
          }
        }, 30000); // 30 seconds
        
        ws.current.pingInterval = pingInterval;
      };
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message:', data);
          setLastMessage(data);
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };
      
      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };
      
      ws.current.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
        
        // Clear ping interval
        if (ws.current?.pingInterval) {
          clearInterval(ws.current.pingInterval);
        }
        
        // Auto-reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('🔄 Reconnecting WebSocket...');
          connect();
        }, 5000);
      };
      
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  };
  
  useEffect(() => {
    connect();
    
    return () => {
      // Cleanup
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      
      if (ws.current) {
        if (ws.current.pingInterval) {
          clearInterval(ws.current.pingInterval);
        }
        ws.current.close();
      }
    };
  }, []);
  
  const sendMessage = (message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  };
  
  return {
    isConnected,
    lastMessage,
    sendMessage
  };
};

export default useWebSocket;

