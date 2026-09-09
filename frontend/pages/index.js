import React, { useState, useEffect, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL !== undefined && process.env.NEXT_PUBLIC_API_URL !== ''
  ? process.env.NEXT_PUBLIC_API_URL
  : (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '3000'
      ? 'http://localhost:8000'
      : '');

const ChatbotPage = () => {
  // Navigation tab: 'food' or 'booking'
  const [activeTab, setActiveTab] = useState('food');

  // Customer registration state
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [isRegistered, setIsRegistered] = useState(false);
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);

  // Food ordering state
  const [foodMessages, setFoodMessages] = useState([]);
  const [foodInput, setFoodInput] = useState('');
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState([]);
  const [hasReceipt, setHasReceipt] = useState(false);
  const [foodLoading, setFoodLoading] = useState(false);

  // Booking state
  const [bookingMessages, setBookingMessages] = useState([]);
  const [bookingInput, setBookingInput] = useState('');
  const [services, setServices] = useState([]);
  const [bookingState, setBookingState] = useState('GREET');
  const [activeBookingId, setActiveBookingId] = useState(null);
  const [activeMeetLink, setActiveMeetLink] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);

  // My Bookings lookup modal
  const [showMyBookings, setShowMyBookings] = useState(false);
  const [lookupEmail, setLookupEmail] = useState('');
  const [userBookings, setUserBookings] = useState([]);
  const [lookupLoading, setLookupLoading] = useState(false);

  const foodChatRef = useRef(null);
  const bookingChatRef = useRef(null);

  // Initialize session & credentials
  useEffect(() => {
    let sid = localStorage.getItem('cafebot_session_id');
    if (!sid) {
      sid = 'sess_' + Math.random().toString(36).substring(2, 12);
      localStorage.setItem('cafebot_session_id', sid);
    }
    setSessionId(sid);

    const registered = localStorage.getItem('cafebot_registered');
    if (registered === 'true') {
      setIsRegistered(true);
      const name = localStorage.getItem('cafebot_customer_name') || '';
      const phone = localStorage.getItem('cafebot_customer_phone') || '';
      const email = localStorage.getItem('cafebot_customer_email') || '';
      setCustomerName(name);
      setCustomerPhone(phone);
      setCustomerEmail(email);
      setLookupEmail(email);

      setFoodMessages([
        { role: 'bot', content: `Welcome back, ${name}! Ready to order fresh food & drinks at Fireball Cafe?` }
      ]);
      setBookingMessages([
        { role: 'bot', content: `Hello ${name}! I'm your AI Reservation Assistant. Would you like to reserve a table, book a tasting experience, or schedule a masterclass?` }
      ]);
    } else {
      setTimeout(() => setShowCredentialsModal(true), 400);
    }
  }, []);

  // Fetch menu and booking services
  useEffect(() => {
    fetch(`${API_BASE}/api/menu`)
      .then(res => res.json())
      .then(data => setMenu(data.menu || []))
      .catch(() => {
        setMenu([
          {
            category: 'Burger',
            items: [
              { name: 'Cheese Burger', price: 17 },
              { name: 'Spicy Jalapeño', price: 20 },
              { name: 'Smoky BBQ', price: 19 },
              { name: 'Chicken Burger', price: 18 },
              { name: 'Beef Burger', price: 19 }
            ]
          },
          {
            category: 'Fries',
            items: [
              { name: 'Large Fries', price: 13 },
              { name: 'Medium Fries', price: 11 },
              { name: 'Regular Fries', price: 9 }
            ]
          },
          {
            category: 'Drinks',
            items: [
              { name: 'Large Drink', price: 11 },
              { name: 'Medium Drink', price: 9 },
              { name: 'Regular Drink', price: 7 }
            ]
          }
        ]);
      });

    fetch(`${API_BASE}/api/services`)
      .then(res => res.json())
      .then(data => setServices(data || []))
      .catch(err => console.error('Failed to load services:', err));
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    if (activeTab === 'food' && foodChatRef.current) {
      foodChatRef.current.scrollTop = foodChatRef.current.scrollHeight;
    }
    if (activeTab === 'booking' && bookingChatRef.current) {
      bookingChatRef.current.scrollTop = bookingChatRef.current.scrollHeight;
    }
  }, [foodMessages, bookingMessages, activeTab]);

  // Handle registration
  const handleRegister = async (e) => {
    e.preventDefault();
    if (!customerName.trim() || !customerPhone.trim()) {
      alert('Please enter your name and phone number');
      return;
    }

    try {
      await fetch(`${API_BASE}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          customer_phone: customerPhone,
          session_id: sessionId
        })
      });

      localStorage.setItem('cafebot_registered', 'true');
      localStorage.setItem('cafebot_customer_name', customerName);
      localStorage.setItem('cafebot_customer_phone', customerPhone);
      if (customerEmail) {
        localStorage.setItem('cafebot_customer_email', customerEmail);
        setLookupEmail(customerEmail);
      }

      setIsRegistered(true);
      setShowCredentialsModal(false);

      setFoodMessages([
        { role: 'bot', content: `Welcome ${customerName}! What would you like to order today?` }
      ]);
      setBookingMessages([
        { role: 'bot', content: `Welcome ${customerName}! How can I help with your reservation or appointment booking?` }
      ]);
    } catch (err) {
      console.error('Registration failed:', err);
      setIsRegistered(true);
      setShowCredentialsModal(false);
    }
  };

  // Send Food Ordering message
  const handleSendFood = async () => {
    if (!foodInput.trim() || foodLoading) return;
    const text = foodInput.trim();
    setFoodInput('');
    setFoodMessages(prev => [...prev, { role: 'user', content: text }]);
    setFoodLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/cafe/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        })
      });
      const data = await res.json();
      if (data.cart_items) setCart(data.cart_items);
      if (data.has_receipt) setHasReceipt(true);

      setFoodMessages(prev => [
        ...prev,
        {
          role: 'bot',
          content: data.reply || data.response,
          isReceipt: data.has_receipt
        }
      ]);
    } catch (err) {
      console.error('Food chat error:', err);
      setFoodMessages(prev => [
        ...prev,
        { role: 'bot', content: 'Sorry, I had trouble processing your order. Please try again.' }
      ]);
    } finally {
      setFoodLoading(false);
    }
  };

  // Quick add item to cart
  const handleQuickAdd = async (itemName) => {
    const text = `I would like to order 1 ${itemName}`;
    setFoodMessages(prev => [...prev, { role: 'user', content: text }]);
    setFoodLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/cafe/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      const data = await res.json();
      if (data.cart_items) setCart(data.cart_items);
      setFoodMessages(prev => [...prev, { role: 'bot', content: data.reply || data.response }]);
    } catch (err) {
      console.error(err);
    } finally {
      setFoodLoading(false);
    }
  };

  // Send Booking message
  const handleSendBooking = async (overrideText) => {
    const text = (overrideText || bookingInput).trim();
    if (!text || bookingLoading) return;
    if (!overrideText) setBookingInput('');

    setBookingMessages(prev => [...prev, { role: 'user', content: text }]);
    setBookingLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId
        })
      });
      const data = await res.json();

      setBookingState(data.state || 'GREET');
      if (data.booking_id) setActiveBookingId(data.booking_id);
      if (data.meet_link) setActiveMeetLink(data.meet_link);
      if (data.services && data.services.length > 0) setServices(data.services);

      setBookingMessages(prev => [
        ...prev,
        {
          role: 'bot',
          content: data.reply,
          state: data.state,
          bookingId: data.booking_id,
          meetLink: data.meet_link,
          collectedData: data.collected_data
        }
      ]);
    } catch (err) {
      console.error('Booking chat error:', err);
      setBookingMessages(prev => [
        ...prev,
        { role: 'bot', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    } finally {
      setBookingLoading(false);
    }
  };

  const handleSelectService = (serviceName) => {
    handleSendBooking(`I want to book ${serviceName}`);
  };

  const handleFetchBookings = async () => {
    if (!lookupEmail.trim()) return;
    setLookupLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/bookings?email=${encodeURIComponent(lookupEmail.trim())}`);
      const data = await res.json();
      setUserBookings(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Lookup error:', err);
      setUserBookings([]);
    } finally {
      setLookupLoading(false);
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!confirm('Are you sure you want to cancel this booking?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/bookings/${bookingId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        alert('Booking cancelled successfully');
        handleFetchBookings();
      }
    } catch (err) {
      console.error('Cancel error:', err);
    }
  };

  return (
    <div style={{ fontFamily: 'Segoe UI, Roboto, Helvetica, Arial, sans-serif', backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
      {showCredentialsModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white', padding: '30px', borderRadius: '12px',
            width: '420px', boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
          }}>
            <h2 style={{ textAlign: 'center', color: '#db1020', margin: '0 0 10px 0' }}>Welcome to Fireball!</h2>
            <p style={{ textAlign: 'center', color: '#666', fontSize: '14px', marginBottom: '20px' }}>
              Enter your details for food ordering and table reservations
            </p>
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', color: '#333' }}>Name *</label>
                <input
                  type="text"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                  placeholder="e.g. John Doe"
                  style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                  required
                />
              </div>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', color: '#333' }}>Phone *</label>
                <input
                  type="tel"
                  value={customerPhone}
                  onChange={e => setCustomerPhone(e.target.value)}
                  placeholder="e.g. +1 555-0199"
                  style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                  required
                />
              </div>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', color: '#333' }}>Email (for appointments)</label>
                <input
                  type="email"
                  value={customerEmail}
                  onChange={e => setCustomerEmail(e.target.value)}
                  placeholder="e.g. john@example.com"
                  style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ccc', boxSizing: 'border-box' }}
                />
              </div>
              <button
                type="submit"
                style={{
                  width: '100%', padding: '12px', backgroundColor: '#db1020',
                  color: 'white', fontSize: '16px', fontWeight: 'bold',
                  border: 'none', borderRadius: '6px', cursor: 'pointer'
                }}
              >
                Get Started
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header Bar */}
      <header style={{ backgroundColor: '#ffffff', borderBottom: '2px solid #eaeaea', padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <img src="/logo.png" alt="Fireball Fast Food" style={{ height: '48px', objectFit: 'contain' }} />
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', color: '#db1020', fontWeight: 'bold' }}>Fireball Cafe & Reservations</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>AI-Powered Food Ordering & Table/Appointment Booking</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', gap: '8px', backgroundColor: '#f0f2f5', padding: '4px', borderRadius: '8px' }}>
          <button
            onClick={() => setActiveTab('food')}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer',
              backgroundColor: activeTab === 'food' ? '#db1020' : 'transparent',
              color: activeTab === 'food' ? 'white' : '#555',
              transition: 'all 0.2s'
            }}
          >
            🍔 Food & Drinks
          </button>
          <button
            onClick={() => setActiveTab('booking')}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer',
              backgroundColor: activeTab === 'booking' ? '#db1020' : 'transparent',
              color: activeTab === 'booking' ? 'white' : '#555',
              transition: 'all 0.2s'
            }}
          >
            📅 Table & Appointments
          </button>
        </div>

        <div>
          <button
            onClick={() => {
              setShowMyBookings(true);
              if (customerEmail) handleFetchBookings();
            }}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ffd700',
              color: '#333',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            📋 My Bookings
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ maxWidth: '1400px', margin: '15px auto', padding: '0 15px', height: 'calc(100vh - 100px)' }}>

        {/* TAB 1: FOOD ORDERING */}
        {activeTab === 'food' && (
          <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
            
            {/* Menu Section */}
            <div style={{ flex: 1, backgroundColor: 'white', borderRadius: '10px', padding: '20px', overflowY: 'auto', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
              <div style={{ backgroundColor: '#db1020', color: 'white', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px', marginBottom: '15px' }}>
                🍔 Fireball Menu
              </div>

              {menu.map((cat, idx) => (
                <div key={idx} style={{ marginBottom: '20px' }}>
                  <h3 style={{ borderBottom: '2px solid #ffd700', paddingBottom: '4px', color: '#db1020', margin: '10px 0' }}>
                    {cat.category}
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' }}>
                    {cat.items.map((item, i) => (
                      <div
                        key={i}
                        onClick={() => handleQuickAdd(item.name)}
                        style={{
                          border: '1px solid #eaeaea',
                          borderRadius: '8px',
                          padding: '12px',
                          backgroundColor: '#fafafa',
                          cursor: 'pointer',
                          transition: 'transform 0.15s, border-color 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = '#db1020'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = '#eaeaea'; e.currentTarget.style.transform = 'translateY(0)'; }}
                      >
                        <div style={{ fontWeight: 'bold', color: '#222', display: 'flex', justifyContent: 'space-between' }}>
                          <span>{item.name}</span>
                          <span style={{ color: '#db1020' }}>${item.price}</span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#777', marginTop: '6px' }}>Click to add +1 to cart</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat & Cart Section */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: 'white', borderRadius: '10px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
              <div style={{ backgroundColor: '#ffd700', color: '#222', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px' }}>
                💬 Chat with CafeBot
              </div>

              {/* Cart Drawer */}
              {cart.length > 0 && (
                <div style={{ backgroundColor: '#fff9e6', border: '1px solid #ffe082', borderRadius: '8px', padding: '12px', marginTop: '12px' }}>
                  <div style={{ fontWeight: 'bold', color: '#996500', marginBottom: '6px' }}>🛒 Current Cart:</div>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '14px', color: '#333' }}>
                    {cart.map((item, idx) => (
                      <li key={idx}>
                        <strong>{item.quantity}x</strong> {item.name} — ${item.price * item.quantity}
                      </li>
                    ))}
                  </ul>
                  <div style={{ marginTop: '8px', fontWeight: 'bold', borderTop: '1px solid #ffe082', paddingTop: '6px', textAlign: 'right', color: '#db1020' }}>
                    Total: ${cart.reduce((s, i) => s + (i.price * i.quantity), 0)}
                  </div>
                </div>
              )}

              {/* Chat Messages */}
              <div
                ref={foodChatRef}
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  padding: '12px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '8px',
                  marginTop: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                {foodMessages.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '80%',
                      backgroundColor: msg.role === 'user' ? '#ffe082' : '#ffffff',
                      color: '#222',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                      whiteSpace: 'pre-wrap',
                      lineHeight: '1.4'
                    }}
                  >
                    {msg.content}
                  </div>
                ))}
                {foodLoading && (
                  <div style={{ alignSelf: 'flex-start', color: '#888', fontStyle: 'italic', fontSize: '13px' }}>
                    CafeBot is typing...
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <input
                  type="text"
                  value={foodInput}
                  onChange={e => setFoodInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendFood()}
                  placeholder="e.g. 2 Cheese Burgers and 1 Large Fries..."
                  style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc', fontSize: '15px' }}
                />
                <button
                  onClick={handleSendFood}
                  disabled={foodLoading}
                  style={{
                    backgroundColor: '#db1020',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0 24px',
                    fontWeight: 'bold',
                    fontSize: '18px',
                    cursor: 'pointer'
                  }}
                >
                  ➤
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TABLE & APPOINTMENT BOOKING */}
        {activeTab === 'booking' && (
          <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
            
            {/* Services Quick Selection Panel */}
            <div style={{ flex: 1, backgroundColor: 'white', borderRadius: '10px', padding: '20px', overflowY: 'auto', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
              <div style={{ backgroundColor: '#db1020', color: 'white', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px', marginBottom: '15px' }}>
                📅 Available Reservations & Services
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {services.map((svc) => (
                  <div
                    key={svc.id}
                    onClick={() => handleSelectService(svc.name)}
                    style={{
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '16px',
                      backgroundColor: '#f8fafc',
                      cursor: 'pointer',
                      transition: 'all 0.15s'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = '#db1020'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = '#e2e8f0'; e.currentTarget.style.transform = 'translateY(0)'; }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ margin: 0, fontSize: '16px', color: '#1e293b' }}>{svc.name}</h3>
                      <span style={{ backgroundColor: '#e2e8f0', color: '#475569', fontSize: '12px', fontWeight: 'bold', padding: '4px 8px', borderRadius: '12px' }}>
                        ⏱ {svc.duration_minutes} min
                      </span>
                    </div>
                    <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#64748b' }}>{svc.description}</p>
                    <div style={{ marginTop: '10px', color: '#db1020', fontSize: '13px', fontWeight: '600' }}>
                      Click to start booking →
                    </div>
                  </div>
                ))}
              </div>

              {/* Status indicator */}
              <div style={{ marginTop: '20px', padding: '14px', backgroundColor: '#f1f5f9', borderRadius: '8px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>
                  🤖 LangGraph State: <span style={{ color: '#db1020' }}>{bookingState}</span>
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  The AI assistant validates dates, slots, contacts, and creates calendar events automatically.
                </div>
              </div>
            </div>

            {/* AI Booking Chat */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: 'white', borderRadius: '10px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
              <div style={{ backgroundColor: '#db1020', color: 'white', padding: '10px 16px', borderRadius: '6px', fontWeight: 'bold', fontSize: '18px' }}>
                🤖 AI Reservation & Booking Assistant
              </div>

              {/* Chat Messages */}
              <div
                ref={bookingChatRef}
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  padding: '12px',
                  backgroundColor: '#f9f9f9',
                  borderRadius: '8px',
                  marginTop: '12px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                {bookingMessages.map((msg, i) => (
                  <div
                    key={i}
                    style={{
                      alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      maxWidth: '85%',
                      backgroundColor: msg.role === 'user' ? '#db1020' : '#ffffff',
                      color: msg.role === 'user' ? '#ffffff' : '#222',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                      whiteSpace: 'pre-wrap',
                      lineHeight: '1.4'
                    }}
                  >
                    {msg.content}

                    {/* Booking Confirmation Card */}
                    {msg.bookingId && (
                      <div style={{
                        marginTop: '12px',
                        padding: '14px',
                        backgroundColor: '#f0fdf4',
                        border: '1px solid #bbf7d0',
                        borderRadius: '8px',
                        color: '#166534'
                      }}>
                        <div style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '6px' }}>
                          ✅ Booking Confirmed!
                        </div>
                        <div style={{ fontSize: '13px' }}><strong>Booking ID:</strong> {msg.bookingId}</div>
                        {msg.meetLink && (
                          <div style={{ marginTop: '8px' }}>
                            <a
                              href={msg.meetLink}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                display: 'inline-block',
                                backgroundColor: '#16a34a',
                                color: 'white',
                                padding: '6px 14px',
                                borderRadius: '6px',
                                textDecoration: 'none',
                                fontWeight: 'bold',
                                fontSize: '13px'
                              }}
                            >
                              🎥 Join Google Meet
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {bookingLoading && (
                  <div style={{ alignSelf: 'flex-start', color: '#888', fontStyle: 'italic', fontSize: '13px' }}>
                    AI is planning your reservation...
                  </div>
                )}
              </div>

              {/* Input Area */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
                <input
                  type="text"
                  value={bookingInput}
                  onChange={e => setBookingInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendBooking()}
                  placeholder="e.g. Table for 4 tomorrow at 7:00 PM, or John Doe john@test.com..."
                  style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc', fontSize: '15px' }}
                />
                <button
                  onClick={() => handleSendBooking()}
                  disabled={bookingLoading}
                  style={{
                    backgroundColor: '#db1020',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0 24px',
                    fontWeight: 'bold',
                    fontSize: '18px',
                    cursor: 'pointer'
                  }}
                >
                  ➤
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* My Bookings Modal */}
      {showMyBookings && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white', padding: '24px', borderRadius: '12px',
            width: '600px', maxHeight: '80vh', display: 'flex', flexDirection: 'column',
            boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0, color: '#db1020', fontSize: '20px' }}>📋 My Bookings & Reservations</h2>
              <button
                onClick={() => setShowMyBookings(false)}
                style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#888' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <input
                type="email"
                value={lookupEmail}
                onChange={e => setLookupEmail(e.target.value)}
                placeholder="Enter your email to look up bookings..."
                style={{ flex: 1, padding: '10px', borderRadius: '6px', border: '1px solid #ccc' }}
              />
              <button
                onClick={handleFetchBookings}
                disabled={lookupLoading}
                style={{
                  backgroundColor: '#db1020', color: 'white', border: 'none',
                  borderRadius: '6px', padding: '0 16px', fontWeight: 'bold', cursor: 'pointer'
                }}
              >
                Search
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {lookupLoading && <div style={{ textAlign: 'center', color: '#666' }}>Loading your bookings...</div>}
              {!lookupLoading && userBookings.length === 0 && (
                <div style={{ textAlign: 'center', color: '#999', padding: '20px 0' }}>
                  No bookings found for this email.
                </div>
              )}
              {userBookings.map((b) => (
                <div key={b.id} style={{
                  border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px',
                  backgroundColor: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 'bold', color: '#1e293b' }}>{b.service_name || 'Reservation'}</div>
                    <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                      📅 {b.appointment_date} at ⏰ {b.appointment_time}
                    </div>
                    <div style={{ fontSize: '12px', color: '#888', marginTop: '2px' }}>
                      Status: <span style={{ color: b.status === 'confirmed' ? 'green' : '#db1020', fontWeight: 'bold' }}>{b.status}</span>
                    </div>
                    {b.meet_link && (
                      <div style={{ marginTop: '6px' }}>
                        <a href={b.meet_link} target="_blank" rel="noreferrer" style={{ fontSize: '12px', color: '#2563eb', textDecoration: 'underline' }}>
                          🎥 Join Google Meet
                        </a>
                      </div>
                    )}
                  </div>
                  {b.status !== 'cancelled' && (
                    <button
                      onClick={() => handleCancelBooking(b.id)}
                      style={{
                        backgroundColor: '#fee2e2', color: '#b91c1c', border: 'none',
                        borderRadius: '6px', padding: '6px 12px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotPage;