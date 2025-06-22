import React, { useState, useEffect, useRef } from 'react';

const ChatbotPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState([]);
  const [sessionId, setSessionId] = useState('');
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [isRegistered, setIsRegistered] = useState(false);
  const [hasReceipt, setHasReceipt] = useState(false);
  
  const chatContainerRef = useRef(null);

  // Generate or retrieve session ID
  useEffect(() => {
    const storedSessionId = localStorage.getItem('cafebot_session_id');
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      const newSessionId = Math.random().toString(36).substring(2, 15) + 
                          Math.random().toString(36).substring(2, 15);
      localStorage.setItem('cafebot_session_id', newSessionId);
      setSessionId(newSessionId);
    }
  
    // Check if user is registered
    const registered = localStorage.getItem('cafebot_registered');
    if (registered === 'true') {
      setIsRegistered(true);
      const name = localStorage.getItem('cafebot_customer_name') || '';
      const phone = localStorage.getItem('cafebot_customer_phone') || '';
      setCustomerName(name);
      setCustomerPhone(phone);
      
      // Personalized welcome message
      setMessages([
        { role: 'bot', content: `Welcome ${name}! to FireBall, ready to take your order.` }
      ]);
    } else {
      setTimeout(() => {
        setShowCredentialsModal(true);
      }, 500);
    }
  }, []);
  
  // Fetch menu
  useEffect(() => {
    fetch('http://localhost:8000/menu')
      .then(res => res.json())
      .then(data => setMenu(data.menu || []));
  }, []);

  // Auto-scroll to the latest message
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle customer registration
  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!customerName || !customerPhone) {
      alert('Please enter both your name and phone number');
      return;
    }
    
    try {
      const response = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          customer_phone: customerPhone,
          session_id: sessionId
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        localStorage.setItem('cafebot_registered', 'true');
        localStorage.setItem('cafebot_customer_name', customerName);
        localStorage.setItem('cafebot_customer_phone', customerPhone);
        
        setIsRegistered(true);
        setShowCredentialsModal(false);
        
        // Add welcome message
        setMessages(prev => [...prev, { role: 'bot', content: data.message || 'Welcome! How can I help you today?' }]);
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('There was an error registering your information. Please try again.');
    }
  };

  // Handle sending messages
  const handleSend = async () => { 
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    
    const userInput = input;
    setInput(''); // Clear input field

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userInput,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const data = await response.json();
      
      // Update cart state
      if (data.cart_items) {
        setCart(data.cart_items);
      }
      
      // Check if receipt was generated
      if (data.has_receipt) {
        setHasReceipt(true);
      }
      
      // Add bot response to chat
      const botMessage = { 
        role: 'bot', 
        content: data.response,
        isReceipt: data.has_receipt
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat request error:', error);
      const errorMessage = { 
        role: 'bot', 
        content: 'Sorry, I encountered an error processing your request. Please try again.' 
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Start new order after receipt
  const handleStartNewOrder = () => {
    setHasReceipt(false);
    setMessages(prev => [...prev, { 
      role: 'bot', 
      content: 'What would you like to order?' 
    }]);
  };

  // Format receipt text for better display
  const formatReceiptContent = (receiptText) => {
    if (!receiptText.includes('----- Receipt -----')) return receiptText;

    const parts = receiptText.split('\n');
    return (
      <div className="receipt">
        <h3>Your Receipt</h3>
        {parts.map((line, index) => {
          if (line.includes('----- Receipt -----') || line.includes('---------------------')) {
            return null;
          }
          if (line.includes('Order ID:') || line.includes('Total:')) {
            return <strong key={index}>{line}<br/></strong>;
          }
          return <span key={index}>{line}<br/></span>;
        })}
      </div>
    );
  };

  return (
    <div style={{ fontFamily: 'Arial, sans-serif' }}>
      {/* Credentials Modal */}
      {showCredentialsModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '15px',
            width: '400px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ textAlign: 'center', color: '#db1020' }}>Welcome to CafeBot!</h2>
            <p style={{ textAlign: 'center', color: 'black' }}>Please enter your details to continue</p>
            
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: 'black' }}>
                  Your Name:
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    fontSize: '16px',
                    borderRadius: '5px',
                    border: '1px solid #ccc'
                  }}
                  required
                />
              </div>
              
              <div style={{ marginBottom: '25px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: 'black' }}>
                  Phone Number:
                </label>
                <input
                  type="tel"
                  value={customerPhone}
                  onChange={e => setCustomerPhone(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '10px', 
                    fontSize: '16px',
                    borderRadius: '5px',
                    border: '1px solid #ccc',
                    color: 'black'
                  }}
                  required
                />
              </div>
              
              <button
                type="submit"
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: '#ffd700',
                  color: 'black',
                  fontSize: '18px',
                  fontWeight: 'bold',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  color: 'black'
                }}
              >
                Continue
              </button>
            </form>
          </div>
        </div>
      )}

{/* Top Bar */}
<div style={{ backgroundColor: '#ffd700', padding: '0px', textAlign: 'center', color: 'black' }}>
  <img 
    src="/logo.png" 
    alt="Fireball Fast Food" 
    style={{ 
      width: '200px', // Increased width for better readability
      height: 'auto', 
      marginBottom: '0px', 
      display: 'block', // Ensures the image behaves as a block element
      margin: '0 auto', // Centers the image horizontally
    }}
  />
</div>

      <div style={{ display: 'flex', height: '90vh' }}>
        {/* Menu Section */}
        <div style={{ width: '50%', borderRight: '1px solid #ccc', padding: '15px', overflowY: 'auto', backgroundColor: 'white', color: 'black' }}>
          <div style={{ backgroundColor: '#db1020', color: 'white', padding: '10px', textAlign: 'center', fontSize: '20px', fontWeight: 'bold' }}>
            Menu
          </div>
          <div style={{ marginTop: '10px' }}>
            <h3>Burger</h3>
            <p><strong>Cheese Burger:</strong>----- $17<br />|-<i>Juicy beef patty with melted cheddar, lettuce, and tomato on a soft bun.</i></p>
            <p><strong>Spicy Jalapeño:</strong>----- $20<br />|-<i>Adds fiery jalapeños and pepper jack cheese for a bold kick.</i></p>
            <p><strong>Smoky BBQ:</strong>----- $19<br />|-<i>Features smoky BBQ sauce and crispy onion rings with cheddar.</i></p>
            <p><strong>Non-Cheese Burger:</strong>----- $16<br />|-<i>Classic beef patty with crisp lettuce, tomato, and mayo on a bun.</i></p>
            <p><strong>Garlic Mushroom:</strong>----- $19<br />|-<i>Topped with sautéed garlic mushrooms and tangy aioli.</i></p>
            <p><strong>Avocado Ranch:</strong>----- $20<br />|-<i>Includes creamy avocado and cool ranch dressing for freshness.</i></p>
            <p><strong>Chicken Burger:</strong>----- $18<br />|-<i>Tender grilled or crispy chicken with lettuce and mayo on a toasted bun.</i></p>
            <p><strong>Buffalo Heat:</strong>----- $20<br />|-<i>Tossed in spicy buffalo sauce with blue cheese crumbles.</i></p>
            <p><strong>Honey Mustard Glaze:</strong>----- $20<br />|-<i>Drizzled with sweet honey mustard and pickled onions.</i></p>
            <p><strong>Beef Burger:</strong>----- $19<br />|-<i>Hearty beef patty with fresh lettuce, tomato, and pickles on a fluffy bun.</i></p>
            <p><strong>Bacon Jam Bliss:</strong>----- $20<br />|-<i>Layered with sweet-savory bacon jam and arugula.</i></p>
            <p><strong>Truffle Deluxe:</strong>----- $20<br />|-<i>Enhanced with truffle aioli and caramelized onions.</i></p>

            <h3><strong>Fries</strong></h3>
            <p>Large: ----- $13<br />Medium: ------ $11<br />Regular: ----- $9</p>

            <h3><strong>Drinks</strong></h3>
            <p>Pepsi, Sprite, Coca-Cola, Fanta<br />Large: ----- $11<br />Medium: ----- $9<br />Regular: ----- $7</p>
          </div>
        </div>

        {/* Chat Section */}
        <div style={{ width: '50%', display: 'flex', flexDirection: 'column', padding: '15px', backgroundColor: 'white', color: 'black' }}>
          <div style={{ backgroundColor: '#db1020', padding: '10px', textAlign: 'center', fontSize: '20px', fontWeight: 'bold', color: 'white' }}>
            Order Please !
          </div>

          {/* Cart summary (if items exist) */}
          {cart.length > 0 && (
            <div style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '10px', 
              margin: '10px 0', 
              borderRadius: '8px',
              border: '1px solid #ddd'
            }}>
              <h4 style={{ margin: '0 0 10px 0' }}>Your Cart</h4>
              <ul style={{ margin: 0, padding: '0 0 0 20px' }}>
                {cart.map((item, index) => (
                  <li key={index}>
                    {item.quantity}x {item.name} - ${item.price * item.quantity}
                  </li>
                ))}
              </ul>
              <div style={{ 
                marginTop: '10px', 
                fontWeight: 'bold', 
                borderTop: '1px solid #ddd', 
                paddingTop: '10px' 
              }}>
                Total: ${cart.reduce((sum, item) => sum + (item.price * item.quantity), 0)}
              </div>
            </div>
          )}

          {/* Chat messages */}
          <div 
            ref={chatContainerRef}
            style={{ 
              flex: 1, 
              overflowY: 'auto', 
              padding: '10px', 
              marginTop: '10px', 
              backgroundColor: '#f9f9f9', 
              borderRadius: '10px', 
              display: 'flex', 
              flexDirection: 'column' 
            }}
          >
            {messages.map((msg, i) => (
              <div key={i} style={{
                backgroundColor: msg.role === 'user' ? '#ffe082' : '#dcedc8',
                color: 'black',
                padding: '10px',
                margin: '10px 0',
                borderRadius: '15px',
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '70%',
                textAlign: msg.role === 'user' ? 'right' : 'left'
              }}>
                {msg.isReceipt ? formatReceiptContent(msg.content) : msg.content}
              </div>
            ))}
          </div>

          {/* "Start New Order" button after receipt */}
          {hasReceipt && (
            <div style={{ textAlign: 'center', margin: '10px 0' }}>
              <button
                onClick={handleStartNewOrder}
                style={{
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  padding: '10px 20px',
                  fontSize: '16px',
                  borderRadius: '5px',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                Start New Order
              </button>
            </div>
          )}

          {/* Message input */}
          <div style={{ display: 'flex', marginTop: '10px' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your order..."
              style={{ 
                flex: 1, 
                padding: '10px', 
                fontSize: '16px', 
                borderRadius: '10px', 
                border: '1px solid #ccc' 
              }}
              onKeyPress={e => e.key === 'Enter' && handleSend()}
            />
            <button
              onClick={handleSend}
              style={{ 
                marginLeft: '10px', 
                backgroundColor: '#ffd700', 
                color: 'black', 
                fontSize: '20px', 
                padding: '0 20px', 
                borderRadius: '10px', 
                border: 'none',
                cursor: 'pointer'
              }}
            >
              ➢
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotPage;