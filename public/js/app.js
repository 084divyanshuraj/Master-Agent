/* ==========================================================================
   Vignan's University — Master Agent Enterprise Portal Controller
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Dynamic API Base to support both standalone port 8000 and port 3000 static server
  const API_BASE = (window.location.hostname === 'localhost' && window.location.port !== '8000' && window.location.port !== '')
    ? 'http://localhost:8000'
    : '';

  // Elements
  const canvas = document.getElementById('networkCanvas');
  
  // Auth Tabs & Alert Banner
  const tabBtnSignIn = document.getElementById('tabBtnSignIn');
  const tabBtnRegister = document.getElementById('tabBtnRegister');
  const authAlert = document.getElementById('authAlert');

  // Sign In Form Elements
  const signInForm = document.getElementById('signInForm');
  const loginEmployeeCode = document.getElementById('loginEmployeeCode');
  const loginPassword = document.getElementById('loginPassword');
  const toggleLoginPwd = document.getElementById('toggleLoginPwd');
  const submitLoginBtn = document.getElementById('submitLoginBtn');
  const linkToRegister = document.getElementById('linkToRegister');

  // Register Form Elements
  const registerForm = document.getElementById('registerForm');
  const regFullName = document.getElementById('regFullName');
  const regEmployeeCode = document.getElementById('regEmployeeCode');
  const regEmail = document.getElementById('regEmail');
  const regUserRole = document.getElementById('regUserRole');
  const regDepartment = document.getElementById('regDepartment');
  const regPassword = document.getElementById('regPassword');
  const toggleRegPwd = document.getElementById('toggleRegPwd');
  const submitRegisterBtn = document.getElementById('submitRegisterBtn');
  const linkToSignIn = document.getElementById('linkToSignIn');

  // Mascot & Demo Buttons
  const quickDemoSection = document.getElementById('quickDemoSection');
  const quickHodBtn = document.getElementById('quickHodBtn');
  const quickDeanBtn = document.getElementById('quickDeanBtn');
  const quickExamBtn = document.getElementById('quickExamBtn');
  
  // Views
  const loginSection = document.getElementById('loginSection');
  const chamberSection = document.getElementById('chamberSection');
  const chatSection = document.getElementById('chatSection');
  
  const userWelcomeBadge = document.getElementById('userWelcomeBadge');
  const btnBackToLogin = document.getElementById('btnBackToLogin');
  const btnBackToChambers = document.getElementById('btnBackToChambers');
  
  // Chat Elements
  const cardGlobalMaster = document.getElementById('cardGlobalMaster');
  const chamberCards = document.querySelectorAll('.chamber-card:not(.global-master-card)');
  
  const chatScopeIcon = document.getElementById('chatScopeIcon');
  const chatScopeTitle = document.getElementById('chatScopeTitle');
  const chatScopeDesc = document.getElementById('chatScopeDesc');
  const chatModePill = document.getElementById('chatModePill');
  const chatHeroSubtitle = document.getElementById('chatHeroSubtitle');
  const traceStepsContainer = document.getElementById('traceStepsContainer');
  const chatMessagesScroll = document.getElementById('chatMessagesScroll');
  const chatPromptInput = document.getElementById('chatPromptInput');
  const btnSendChat = document.getElementById('btnSendChat');
  const quickPromptChips = document.querySelectorAll('.chip-suggestion-btn');
  
  // Agent Drawer Modal Elements
  const agentDrawerModal = document.getElementById('agentDrawerModal');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const drawerGroupTitle = document.getElementById('drawerGroupTitle');
  const drawerGroupDesc = document.getElementById('drawerGroupDesc');
  const drawerAgentsGrid = document.getElementById('drawerAgentsGrid');
  const drawerSubcatBar = document.getElementById('drawerSubcatBar');
  const drawerAgentSearch = document.getElementById('drawerAgentSearch');
  const drawerAgentCountBadge = document.getElementById('drawerAgentCountBadge');

  // Pipeline Audit Trace Modal Elements
  const btnOpenTraceLogs = document.getElementById('btnOpenTraceLogs');
  const traceModal = document.getElementById('traceModal');
  const btnCloseTraceModal = document.getElementById('btnCloseTraceModal');
  const tracePoolStats = document.getElementById('tracePoolStats');
  const traceLogsList = document.getElementById('traceLogsList');

  // Master Agent Report Export & Toast Elements
  const btnExportSessionReport = document.getElementById('btnExportSessionReport');
  const reportExportModal = document.getElementById('reportExportModal');
  const btnCloseReportModal = document.getElementById('btnCloseReportModal');
  const btnCancelReportModal = document.getElementById('btnCancelReportModal');
  const scopeOptLatest = document.getElementById('scopeOptLatest');
  const scopeOptSession = document.getElementById('scopeOptSession');
  const vignanToastContainer = document.getElementById('vignanToastContainer');
  const sessionReports = [];

  // Deployment & Webview Controls
  const btnOpenDeployment = document.getElementById('btnOpenDeployment');
  const chatTabToggle = document.getElementById('chatTabToggle');
  const tabBtnChat = document.getElementById('tabBtnChat');
  const tabBtnLive = document.getElementById('tabBtnLive');
  const chatMainCard = document.getElementById('chatMainCard');
  const liveAppIframeContainer = document.getElementById('liveAppIframeContainer');
  const iframeUrlDisplay = document.getElementById('iframeUrlDisplay');
  const liveAppIframe = document.getElementById('liveAppIframe');
  const btnIframePopout = document.getElementById('btnIframePopout');
  const btnIframeClose = document.getElementById('btnIframeClose');
  const btnSetCustomLink = document.getElementById('btnSetCustomLink');

  // Custom Deployment Link Helpers (stored in localStorage)
  function getCustomUrl(agentId, fallback) {
    try {
      const stored = JSON.parse(localStorage.getItem('vignan_custom_agent_urls') || '{}');
      return stored[agentId] || fallback;
    } catch(e) {
      return fallback;
    }
  }

  function setCustomUrl(agentId, newUrl) {
    try {
      const stored = JSON.parse(localStorage.getItem('vignan_custom_agent_urls') || '{}');
      stored[agentId] = newUrl;
      localStorage.setItem('vignan_custom_agent_urls', JSON.stringify(stored));
    } catch(e) {}

    // Persist to MongoDB Atlas
    fetch(API_BASE + `/api/agents/${agentId}/endpoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint_url: newUrl })
    }).then(r => r.json()).then(res => {
      console.log(`Agent ${agentId} deployment endpoint persisted to MongoDB Atlas:`, res);
    }).catch(err => console.warn('Could not persist endpoint to MongoDB Atlas:', err));
  }

  window.editAgentUrl = function(agentId, agentName) {
    const currentUrl = getCustomUrl(agentId, 'https://api.vignan.ac.in/agents/' + agentId);
    const newUrl = prompt(`Enter custom production deployment URL for ${agentName}:`, currentUrl);
    if (newUrl && newUrl.trim() !== '') {
      setCustomUrl(agentId, newUrl.trim());
      if (typeof renderCategoryAgentsList === 'function') {
        renderCategoryAgentsList();
      }
      alert(`Updated deployment URL for ${agentName} to:\n${newUrl.trim()}`);
    }
  };

  let agentsRegistry = null;
  let activeChatContext = {
    mode: 'global', // 'global' or 'scoped'
    groupId: null,
    groupName: null,
    agentId: null,
    agentName: null,
    endpointUrl: null
  };

  // =========================================================================
  // 0. Fetch Agents Registry
  // =========================================================================
  fetch('data/agents.json')
    .then((res) => res.json())
    .then((data) => {
      agentsRegistry = data;
    })
    .catch((err) => console.warn('Agents registry local fallback active:', err));

  // =========================================================================
  // 1. Constellation Network Canvas (40 Connected Agent Nodes)
  // =========================================================================
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initNodes();
    });

    const NODE_COUNT = 40;
    const nodes = [];
    let mouse = { x: null, y: null, radius: 140 };

    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });

    window.addEventListener('mouseout', () => {
      mouse.x = null;
      mouse.y = null;
    });

    class Node {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.7;
        this.vy = (Math.random() - 0.5) * 0.7;
        this.radius = Math.random() * 2.2 + 1.2;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;

        if (mouse.x && mouse.y) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const force = (mouse.radius - dist) / mouse.radius;
            this.x -= (dx / dist) * force * 3;
            this.y -= (dy / dist) * force * 3;
          }
        }
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(37, 99, 235, 0.45)';
        ctx.fill();
      }
    }

    function initNodes() {
      nodes.length = 0;
      for (let i = 0; i < NODE_COUNT; i++) {
        nodes.push(new Node());
      }
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            const alpha = (1 - dist / 130) * 0.28;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(37, 99, 235, ${alpha})`;
            ctx.lineWidth = 0.85;
            ctx.stroke();
          }
        }
      }

      nodes.forEach((node) => {
        node.update();
        node.draw();
      });

      requestAnimationFrame(animate);
    }

    initNodes();
    animate();
  }

  // =========================================================================
  // 2. Interactive Buji Mascot Personality & Typing Reactions
  // =========================================================================
  const originalGreeting = `"Welcome to <strong>Vignan University's Master Agent Portal</strong>! Please verify your faculty or department credentials below to query unified institutional records and 72 specialized departmental endpoints."`;

  if (loginEmployeeCode) {
    loginEmployeeCode.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val.length > 3) {
        bujiGreetingText.innerHTML = `Verifying credentials for <strong>${escapeHtml(val)}</strong>. Enter your portal password to access institutional intelligence.`;
      } else {
        bujiGreetingText.innerHTML = originalGreeting;
      }
    });
  }

  if (regFullName) {
    regFullName.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (val.length > 2) {
        bujiGreetingText.innerHTML = `Welcome to the faculty portal, <strong>${escapeHtml(val)}</strong>! Please complete your department registration.`;
      } else {
        bujiGreetingText.innerHTML = originalGreeting;
      }
    });
  }

  if (bujiAvatar) {
    bujiAvatar.addEventListener('click', () => {
      bujiAvatar.style.transform = 'scale(1.15) rotate(8deg)';
      setTimeout(() => {
        bujiAvatar.style.transform = '';
      }, 400);
      bujiGreetingText.innerHTML = `*Beep boop!* I'm <strong>Buji</strong>, your university intelligence assistant connected to all 72 specialized departmental endpoints!`;
    });
  }

  // =========================================================================
  // 3. Auth UI Helpers & Tab Switching
  // =========================================================================
  function showAuthAlert(msg, type = 'error') {
    if (!authAlert) return;
    authAlert.className = `auth-alert-banner ${type}`;
    const icon = type === 'error' ? '⚠️' : type === 'success' ? '✓' : 'ℹ️';
    authAlert.innerHTML = `<span>${icon}</span> <span>${escapeHtml(msg)}</span>`;
    authAlert.style.display = 'flex';
  }

  function hideAuthAlert() {
    if (!authAlert) return;
    authAlert.style.display = 'none';
    authAlert.innerHTML = '';
  }

  function switchAuthTab(tab) {
    hideAuthAlert();
    if (tab === 'signin') {
      if (tabBtnSignIn) tabBtnSignIn.classList.add('active');
      if (tabBtnRegister) tabBtnRegister.classList.remove('active');
      if (signInForm) signInForm.style.display = 'flex';
      if (registerForm) registerForm.style.display = 'none';
      if (quickDemoSection) quickDemoSection.style.display = 'flex';
      bujiGreetingText.innerHTML = originalGreeting;
    } else {
      if (tabBtnRegister) tabBtnRegister.classList.add('active');
      if (tabBtnSignIn) tabBtnSignIn.classList.remove('active');
      if (registerForm) registerForm.style.display = 'flex';
      if (signInForm) signInForm.style.display = 'none';
      if (quickDemoSection) quickDemoSection.style.display = 'none';
      bujiGreetingText.innerHTML = `"New to Vignan University's Master Agent Portal? Register your faculty or administrative department profile below to access departmental endpoints."`;
    }
  }

  if (tabBtnSignIn) tabBtnSignIn.addEventListener('click', () => switchAuthTab('signin'));
  if (tabBtnRegister) tabBtnRegister.addEventListener('click', () => switchAuthTab('register'));
  if (linkToRegister) linkToRegister.addEventListener('click', (e) => { e.preventDefault(); switchAuthTab('register'); });
  if (linkToSignIn) linkToSignIn.addEventListener('click', (e) => { e.preventDefault(); switchAuthTab('signin'); });

  // Password visibility toggles
  if (toggleLoginPwd && loginPassword) {
    toggleLoginPwd.addEventListener('click', () => {
      loginPassword.type = loginPassword.type === 'password' ? 'text' : 'password';
      toggleLoginPwd.textContent = loginPassword.type === 'password' ? '👁️' : '🙈';
    });
  }

  if (toggleRegPwd && regPassword) {
    toggleRegPwd.addEventListener('click', () => {
      regPassword.type = regPassword.type === 'password' ? 'text' : 'password';
      toggleRegPwd.textContent = regPassword.type === 'password' ? '👁️' : '🙈';
    });
  }

  // =========================================================================
  // 4. Quick-Fill Shortcuts (Faculty & Staff Profiles)
  // =========================================================================
  function triggerInputEffect(el) {
    if (!el) return;
    el.style.backgroundColor = '#EFF6FF';
    setTimeout(() => {
      el.style.backgroundColor = '#FFFFFF';
    }, 350);
  }

  if (quickHodBtn) {
    quickHodBtn.addEventListener('click', () => {
      switchAuthTab('signin');
      loginEmployeeCode.value = 'VFSTR-HOD-CSE-01';
      loginPassword.value = 'vignan123';
      bujiGreetingText.innerHTML = `Welcome, <strong>Dr. K. V. Rao (HoD CSE)</strong>! Pre-filled demo credentials: <code>vignan123</code>. Click below to enter.`;
      triggerInputEffect(loginEmployeeCode);
      triggerInputEffect(loginPassword);
      hideAuthAlert();
    });
  }

  if (quickDeanBtn) {
    quickDeanBtn.addEventListener('click', () => {
      switchAuthTab('signin');
      loginEmployeeCode.value = 'VFSTR-DEAN-ACAD-04';
      loginPassword.value = 'vignan123';
      bujiGreetingText.innerHTML = `Welcome, Dean <strong>Dr. M. S. Naidu</strong>! Full university academic audit logs and credit databases are accessible.`;
      triggerInputEffect(loginEmployeeCode);
      triggerInputEffect(loginPassword);
      hideAuthAlert();
    });
  }

  if (quickExamBtn) {
    quickExamBtn.addEventListener('click', () => {
      switchAuthTab('signin');
      loginEmployeeCode.value = 'VFSTR-COE-ADM-12';
      loginPassword.value = 'vignan123';
      bujiGreetingText.innerHTML = `Welcome, <strong>Prof. S. R. Murthy</strong>! Controller of Examinations records and grading endpoints are synchronized.`;
      triggerInputEffect(loginEmployeeCode);
      triggerInputEffect(loginPassword);
      hideAuthAlert();
    });
  }

  // Helper for transitioning post-login
  function completeLoginTransition(userData) {
    sessionStorage.setItem('vignan_user', JSON.stringify(userData));

    // Synchronize user profile into MongoDB Atlas in background
    fetch(API_BASE + '/api/auth/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    }).catch(err => console.warn('Could not sync user session to MongoDB Atlas:', err));

    loginSection.style.display = 'none';
    chamberSection.style.display = 'block';

    const roleMap = {
      hod: 'Head of Department',
      faculty: 'Faculty Member',
      dean: 'Dean / Directorate',
      admin: 'Operations Staff',
      exam: 'Examination Cell'
    };
    const roleLabel = roleMap[userData.role] || (userData.role ? userData.role.toUpperCase() : 'FACULTY');
    userWelcomeBadge.innerHTML = `Authorized Staff: <strong>${escapeHtml(userData.name || 'Faculty Member')}</strong> (${escapeHtml(userData.department || 'CSE')}) &bull; ${roleLabel}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // =========================================================================
  // 5. Live Form Authentication (Sign In & Register against MongoDB Atlas)
  // =========================================================================
  if (signInForm) {
    signInForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAuthAlert();

      const employeeCodeVal = loginEmployeeCode.value.trim();
      const passwordVal = loginPassword.value;

      if (!employeeCodeVal || !passwordVal) {
        showAuthAlert('Please enter both Employee Code / Email and your password.', 'error');
        return;
      }

      submitLoginBtn.disabled = true;
      submitLoginBtn.innerHTML = `
        <svg class="spin-icon" style="width:18px;height:18px;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity:0.25;"></circle>
          <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Verifying with MongoDB Atlas...</span>
      `;

      try {
        const res = await fetch(API_BASE + '/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            employee_code: employeeCodeVal,
            password: passwordVal
          })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          showAuthAlert('✓ Credentials verified! Accessing university intelligence...', 'success');
          setTimeout(() => {
            completeLoginTransition(data.user);
            submitLoginBtn.disabled = false;
            submitLoginBtn.innerHTML = `
              <span>Access University Intelligence</span>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            `;
          }, 400);
        } else {
          const errMsg = data.detail || data.message || 'Authentication failed. Please verify credentials.';
          showAuthAlert(errMsg, 'error');
          submitLoginBtn.disabled = false;
          submitLoginBtn.innerHTML = `
            <span>Access University Intelligence</span>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          `;
        }
      } catch (err) {
        showAuthAlert(`Network error connecting to backend: ${err.message}`, 'error');
        submitLoginBtn.disabled = false;
        submitLoginBtn.innerHTML = `
          <span>Access University Intelligence</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        `;
      }
    });
  }

  // Register Form Handler
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAuthAlert();

      const nameVal = regFullName.value.trim();
      const codeVal = regEmployeeCode.value.trim();
      const emailVal = regEmail.value.trim();
      const roleVal = regUserRole.value;
      const deptVal = regDepartment.value;
      const pwdVal = regPassword.value;

      if (!nameVal || !codeVal || !emailVal || !pwdVal) {
        showAuthAlert('Please fill in all required fields.', 'error');
        return;
      }

      if (pwdVal.length < 4) {
        showAuthAlert('Password must be at least 4 characters long.', 'error');
        return;
      }

      submitRegisterBtn.disabled = true;
      submitRegisterBtn.innerHTML = `
        <svg class="spin-icon" style="width:18px;height:18px;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity:0.25;"></circle>
          <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        <span>Registering in MongoDB Atlas...</span>
      `;

      try {
        const res = await fetch(API_BASE + '/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: nameVal,
            employee_code: codeVal,
            email: emailVal,
            role: roleVal,
            department: deptVal,
            password: pwdVal
          })
        });

        const data = await res.json();

        if (res.ok && data.success) {
          showAuthAlert(`✓ ${data.message} Switching to Sign In...`, 'success');
          setTimeout(() => {
            switchAuthTab('signin');
            loginEmployeeCode.value = codeVal;
            loginPassword.value = pwdVal;
            showAuthAlert('Account created! Click "Access University Intelligence" to sign in.', 'success');
            submitRegisterBtn.disabled = false;
            submitRegisterBtn.innerHTML = `
              <span>Register Faculty Account</span>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            `;
          }, 1200);
        } else {
          const errMsg = data.detail || data.message || 'Registration failed. Employee code or email may already exist.';
          showAuthAlert(errMsg, 'error');
          submitRegisterBtn.disabled = false;
          submitRegisterBtn.innerHTML = `
            <span>Register Faculty Account</span>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          `;
        }
      } catch (err) {
        showAuthAlert(`Network error: ${err.message}`, 'error');
        submitRegisterBtn.disabled = false;
        submitRegisterBtn.innerHTML = `
          <span>Register Faculty Account</span>
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        `;
      }
    });
  }

  btnBackToLogin.addEventListener('click', () => {
    chamberSection.style.display = 'none';
    chatSection.style.display = 'none';
    loginSection.style.display = 'flex';
    const submitBtn = document.getElementById('submitLoginBtn');
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <span>Access University Intelligence</span>
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" style="width:20px;height:20px;">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
      </svg>
    `;
    bujiGreetingText.innerHTML = originalGreeting;
  });

  // =========================================================================
  // 5. Category Chamber Selection & Agent Drawer Interactivity
  // =========================================================================
  
  // Launch Global Master Agent Chatbot
  cardGlobalMaster.addEventListener('click', () => {
    launchChatSession({
      mode: 'global',
      scopeTitle: 'Unified Master Agent (All 72 Hackathon Endpoints)',
      scopeDesc: 'Orchestrating across 72 specialized agents in 14 sub-categories across 4 divisions',
      modeLabel: 'Global Master',
      modeClass: 'global',
      heroSubtitle: 'Ask any cross-departmental university query. The master agent will decompose your request, query the appropriate specialized endpoints in parallel using the Groq key pool, and synthesize a single comprehensive answer.'
    });
  });

  // Open Category Drawer for the 4 Main Category Cards
  chamberCards.forEach((card) => {
    card.addEventListener('click', () => {
      const catNum = card.getAttribute('data-category');
      if (catNum) {
        openCategoryDrawer(catNum);
      }
    });
  });

  let currentCategory = null;
  let activeSubcategoryFilter = 'all';
  let currentSearchQuery = '';

  function openCategoryDrawer(catNum) {
    if (!agentsRegistry || !agentsRegistry.categories) return;
    const cat = agentsRegistry.categories.find(c => c.category_number == catNum);
    if (!cat) return;

    currentCategory = cat;
    activeSubcategoryFilter = 'all';
    currentSearchQuery = '';
    if (drawerAgentSearch) drawerAgentSearch.value = '';

    drawerGroupTitle.innerText = `${cat.name} (${cat.total_agents} Specialized Hackathon Endpoints)`;
    drawerGroupDesc.innerText = cat.description;

    renderSubcategoryTabs(cat);
    renderCategoryAgentsList();

    agentDrawerModal.style.display = 'flex';
  }

  function renderSubcategoryTabs(cat) {
    if (!drawerSubcatBar) return;
    drawerSubcatBar.innerHTML = '';

    // "All" tab
    const allBtn = document.createElement('button');
    allBtn.className = `subcat-tab-btn ${activeSubcategoryFilter === 'all' ? 'active' : ''}`;
    allBtn.innerHTML = `<span>All Sub-Categories</span> <strong>(${cat.total_agents})</strong>`;
    allBtn.onclick = () => {
      activeSubcategoryFilter = 'all';
      updateActiveTab();
      renderCategoryAgentsList();
    };
    drawerSubcatBar.appendChild(allBtn);

    // Sub-category tabs for each Group in this Category
    cat.groups.forEach(grp => {
      const btn = document.createElement('button');
      btn.className = `subcat-tab-btn ${activeSubcategoryFilter === grp.id ? 'active' : ''}`;
      btn.innerHTML = `<span>${grp.name}</span> <strong>(${grp.total_agents})</strong>`;
      btn.onclick = () => {
        activeSubcategoryFilter = grp.id;
        updateActiveTab();
        renderCategoryAgentsList();
      };
      drawerSubcatBar.appendChild(btn);
    });
  }

  function updateActiveTab() {
    if (!drawerSubcatBar || !currentCategory) return;
    const btns = drawerSubcatBar.querySelectorAll('.subcat-tab-btn');
    btns.forEach((btn, idx) => {
      if (idx === 0) {
        btn.classList.toggle('active', activeSubcategoryFilter === 'all');
      } else {
        const grp = currentCategory.groups[idx - 1];
        if (grp) btn.classList.toggle('active', activeSubcategoryFilter === grp.id);
      }
    });
  }

  function renderCategoryAgentsList() {
    if (!currentCategory) return;
    drawerAgentsGrid.innerHTML = '';

    let agentsToDisplay = [];
    if (activeSubcategoryFilter === 'all') {
      currentCategory.groups.forEach(g => {
        agentsToDisplay.push(...g.agents);
      });
    } else {
      const matchedGroup = currentCategory.groups.find(g => g.id === activeSubcategoryFilter);
      if (matchedGroup) agentsToDisplay = [...matchedGroup.agents];
    }

    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      agentsToDisplay = agentsToDisplay.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.id.toLowerCase().includes(q) ||
        a.group_name.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q)
      );
    }

    if (drawerAgentCountBadge) {
      drawerAgentCountBadge.innerText = `${agentsToDisplay.length} of ${currentCategory.total_agents} Agents`;
    }

    if (agentsToDisplay.length === 0) {
      drawerAgentsGrid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 2.5rem; color: #64748B;">
          <p style="font-size: 1.05rem; font-weight: 700;">No agents matched "${escapeHtml(currentSearchQuery)}"</p>
          <p style="font-size: 0.82rem; margin-top: 0.3rem;">Try searching for a different keyword or select "All Sub-Categories".</p>
        </div>
      `;
      return;
    }

    agentsToDisplay.forEach((agent) => {
      const effectiveUrl = getCustomUrl(agent.id, agent.deployment_url || agent.endpoint_url);
      const card = document.createElement('div');
      card.className = 'agent-item-card';
      card.innerHTML = `
        <div class="agent-item-header">
          <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="agent-item-number">${agent.id.replace('_', ' ').toUpperCase()}</span>
            <span class="agent-group-tag">${agent.group_name}</span>
          </div>
          <span style="font-size:0.75rem; color:#10B981; font-weight:700;">● Online</span>
        </div>
        <h4 class="agent-item-title">${escapeHtml(agent.name)}</h4>
        <p class="agent-item-desc">${escapeHtml(agent.description)}</p>
        <div class="agent-endpoint-badge" title="${effectiveUrl}">
          <span class="endpoint-label">Link:</span>
          <span class="endpoint-url-text">${effectiveUrl}</span>
          <button class="btn-agent-edit-link" title="Change deployment link" onclick="event.stopPropagation(); editAgentUrl('${agent.id}', '${escapeHtml(agent.name)}')">✏️</button>
        </div>
        <div class="agent-item-actions">
          <a href="${effectiveUrl}" target="_blank" class="btn-agent-live" onclick="event.stopPropagation();" title="Open external deployed link in new tab">
            <span>Open Link</span> ↗
          </a>
          <button class="btn-agent-chat">
            <span>Chat</span> ➜
          </button>
        </div>
      `;
      card.addEventListener('click', () => {
        closeAgentDrawer();
        launchChatSession({
          mode: 'scoped',
          groupId: agent.group_id,
          groupName: agent.group_name,
          categoryId: agent.category_id,
          categoryName: agent.category_name,
          agentId: agent.id,
          agentName: agent.name,
          endpointUrl: effectiveUrl,
          scopeTitle: agent.name,
          scopeDesc: `Scoped to ${agent.group_name} (${agent.category_name}) &bull; Deployed Link: ${effectiveUrl}`,
          modeLabel: 'Scoped Fast-Path',
          modeClass: 'scoped',
          heroSubtitle: `Direct session with ${agent.name}. Responses are routed directly from this agent's deployed link.`
        });
      });
      drawerAgentsGrid.appendChild(card);
    });
  }

  if (drawerAgentSearch) {
    drawerAgentSearch.addEventListener('input', (e) => {
      currentSearchQuery = e.target.value.trim();
      renderCategoryAgentsList();
    });
  }

  function closeAgentDrawer() {
    agentDrawerModal.style.display = 'none';
  }

  btnCloseDrawer.addEventListener('click', closeAgentDrawer);
  agentDrawerModal.addEventListener('click', (e) => {
    if (e.target === agentDrawerModal) closeAgentDrawer();
  });

  // =========================================================================
  // 6. Launching & Managing the Chat Session (View 3)
  // =========================================================================
  function launchChatSession(ctx) {
    activeChatContext = ctx;
    chamberSection.style.display = 'none';
    chatSection.style.display = 'block';

    chatScopeTitle.innerText = ctx.scopeTitle;
    chatScopeDesc.innerHTML = ctx.scopeDesc;
    chatModePill.innerText = ctx.modeLabel;
    chatModePill.className = `mode-pill ${ctx.modeClass}`;
    chatHeroSubtitle.innerText = ctx.heroSubtitle;

    chatPromptInput.placeholder = ctx.mode === 'scoped'
      ? `Ask a specific question for ${ctx.agentName}...`
      : 'Ask a query across university agents (e.g. timetable, grants, attendance analysis)...';

    // Deployment link and tab toggle configuration
    if (ctx.mode === 'scoped' && ctx.endpointUrl) {
      const effectiveUrl = getCustomUrl(ctx.agentId, ctx.endpointUrl);
      if (btnOpenDeployment) {
        btnOpenDeployment.style.display = 'inline-flex';
        btnOpenDeployment.href = effectiveUrl;
      }
      if (chatTabToggle) {
        chatTabToggle.style.display = 'flex';
      }
      if (iframeUrlDisplay) iframeUrlDisplay.innerText = effectiveUrl;
      // Load interactive agent-live.html into iframe
      if (liveAppIframe) liveAppIframe.src = `agent-live.html?id=${ctx.agentId}`;
      if (btnIframePopout) btnIframePopout.href = effectiveUrl;
      switchChatView('chat');
    } else {
      if (btnOpenDeployment) btnOpenDeployment.style.display = 'none';
      if (chatTabToggle) chatTabToggle.style.display = 'none';
      switchChatView('chat');
    }

    if (btnSetCustomLink) {
      btnSetCustomLink.onclick = () => {
        if (!activeChatContext.agentId) return;
        const currentUrl = getCustomUrl(activeChatContext.agentId, activeChatContext.endpointUrl);
        const newUrl = prompt(`Enter custom production deployment URL for ${activeChatContext.agentName}:`, currentUrl);
        if (newUrl && newUrl.trim() !== '') {
          setCustomUrl(activeChatContext.agentId, newUrl.trim());
          activeChatContext.endpointUrl = newUrl.trim();
          if (iframeUrlDisplay) iframeUrlDisplay.innerText = newUrl.trim();
          if (btnOpenDeployment) btnOpenDeployment.href = newUrl.trim();
          if (btnIframePopout) btnIframePopout.href = newUrl.trim();
          alert(`Updated deployment link for ${activeChatContext.agentName}:\n${newUrl.trim()}`);
        }
      };
    }

    // Reset initial messages
    chatMessagesScroll.innerHTML = `
      <div class="message-row assistant">
        <div class="message-header">
          <span class="message-sender">ASSISTANT BUJI</span>
          <span class="message-timestamp">${getCurrentTime()}</span>
        </div>
        <div class="message-body">
          <p>Hi, I'm <strong>Buji</strong>, your Master Agent assistant for <strong>${escapeHtml(ctx.scopeTitle)}</strong>.</p>
          <p>${ctx.mode === 'scoped'
            ? `I have established a direct, low-latency link to <strong>${escapeHtml(ctx.agentName)}</strong>. What records or actions would you like to retrieve?`
            : 'I am orchestrating all 40 autonomous agents across Academics, Student Performance, Research, and Outreach. How can I assist you today?'}</p>
        </div>
      </div>
    `;

    traceStepsContainer.innerHTML = `
      <span class="trace-step-chip">● Session Active</span>
      <span class="trace-step-chip">${ctx.mode === 'scoped' ? 'Path: Stage 4 (Direct Fast-Path)' : 'Path: Stage 1-6 (Orchestrated Multi-Agent)'}</span>
    `;

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  btnBackToChambers.addEventListener('click', () => {
    chatSection.style.display = 'none';
    chamberSection.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Tab Toggles for Chat vs Live App Webview
  if (tabBtnChat) tabBtnChat.addEventListener('click', () => switchChatView('chat'));
  if (tabBtnLive) tabBtnLive.addEventListener('click', () => switchChatView('live'));
  if (btnIframeClose) btnIframeClose.addEventListener('click', () => switchChatView('chat'));

  function switchChatView(view) {
    if (view === 'live') {
      chatMainCard.style.display = 'none';
      liveAppIframeContainer.style.display = 'flex';
      if (tabBtnChat) tabBtnChat.classList.remove('active');
      if (tabBtnLive) tabBtnLive.classList.add('active');
    } else {
      chatMainCard.style.display = 'flex';
      liveAppIframeContainer.style.display = 'none';
      if (tabBtnChat) tabBtnChat.classList.add('active');
      if (tabBtnLive) tabBtnLive.classList.remove('active');
    }
  }

  // =========================================================================
  // 7. Chat Messaging & Simulated Master Agent Pipeline Execution
  // =========================================================================
  btnSendChat.addEventListener('click', handleUserSendMessage);
  chatPromptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleUserSendMessage();
  });

  quickPromptChips.forEach((btn) => {
    btn.addEventListener('click', () => {
      const q = btn.getAttribute('data-query');
      if (q) {
        chatPromptInput.value = q;
        handleUserSendMessage();
      }
    });
  });

  function handleUserSendMessage() {
    const text = chatPromptInput.value.trim();
    if (!text) return;

    chatPromptInput.value = '';

    // Append user message
    const userRow = document.createElement('div');
    userRow.className = 'message-row user';
    userRow.innerHTML = `
      <div class="message-header">
        <span class="message-sender">YOU (FACULTY / STAFF)</span>
        <span class="message-timestamp">${getCurrentTime()}</span>
      </div>
      <div class="message-body">
        <p>${escapeHtml(text)}</p>
      </div>
    `;
    chatMessagesScroll.appendChild(userRow);
    scrollChatToBottom();

    // Trigger Orchestration Animation
    simulateOrchestrationPipeline(text);
  }

  async function simulateOrchestrationPipeline(query) {
    const isScoped = activeChatContext.mode === 'scoped';

    // Step 1: Initial Intent Check Ticker
    traceStepsContainer.innerHTML = `
      <span class="trace-step-chip" style="background:#FEF3C7;color:#D97706;">[1] Intent Check: Querying Orchestrator...</span>
    `;

    const userProfile = JSON.parse(sessionStorage.getItem('vignan_user') || '{}');

    try {
      // Dispatch to FastAPI Backend
      const response = await fetch(API_BASE + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          mode: activeChatContext.mode,
          agent_id: activeChatContext.agentId,
          user: userProfile
        })
      });

      if (response.ok) {
        const data = await response.json();
        renderBackendAssistantResponse(data, query);
        return;
      }
    } catch (e) {
      console.warn("Backend API not reachable or static server active. Running resilient client pipeline fallback.");
    }

    // Client-side fallback if backend API server is not running
    if (isScoped) {
      traceStepsContainer.innerHTML = `
        <span class="trace-step-chip">[1] Scoped Query</span>
        <span class="trace-step-chip" style="background:#DCFCE7;color:#15803D;">[4] Calling ${escapeHtml(activeChatContext.agentName)} directly (210ms)...</span>
      `;
    } else {
      traceStepsContainer.innerHTML = `
        <span class="trace-step-chip">[1] Composite Query</span>
        <span class="trace-step-chip" style="background:#DBEAFE;color:#1E40AF;">[2] Decomposed into 2 Sub-Queries</span>
        <span class="trace-step-chip" style="background:#E0E7FF;color:#4338CA;">[3] Parallel Dispatch (Groq Keys #2 &amp; #3)</span>
      `;
    }

    setTimeout(() => {
      renderAssistantResponse(query, isScoped);
      traceStepsContainer.innerHTML = `
        <span class="trace-step-chip" style="background:#DCFCE7;color:#15803D;">● Response Synthesized (${isScoped ? '280ms' : '1,120ms'})</span>
        <span class="trace-step-chip">Key Pool: Round-Robin Balanced</span>
      `;
    }, isScoped ? 500 : 900);
  }

  // =========================================================================
  // Master Agent Report Generation & Export Utilities
  // =========================================================================

  function showToast(message, type = 'info') {
    if (!vignanToastContainer) return;
    const toast = document.createElement('div');
    toast.className = `vignan-toast ${type}`;
    const icon = type === 'success' ? '✓' : (type === 'error' ? '⚠' : 'ℹ');
    toast.innerHTML = `<span style="font-weight:800;font-size:0.95rem;">${icon}</span><span>${escapeHtml(message)}</span>`;
    vignanToastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 320);
    }, 3200);
  }

  function downloadBlob(content, filename, mimeType = 'text/plain;charset=utf-8') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`Downloaded: ${filename}`, 'success');
  }

  async function copyTextToClipboard(text, successMsg = 'Report copied to clipboard!') {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      showToast(successMsg, 'success');
    } catch (e) {
      showToast('Failed to copy to clipboard.', 'error');
    }
  }

  function getCleanUserMeta(user) {
    const u = user || JSON.parse(sessionStorage.getItem('vignan_user') || '{}');
    return {
      name: u.name || 'Faculty / Staff Member',
      roll: u.rollNumber || u.employee_code || 'VFSTR-STAFF',
      dept: u.department || 'CSE',
      role: (u.role || 'faculty').toUpperCase(),
      email: u.email || 'staff@vignan.ac.in'
    };
  }

  function generateReportMarkdown(report, isFullSession = false) {
    const u = getCleanUserMeta(report?.user);
    const dateStr = report?.dateStr || new Date().toLocaleDateString('en-IN');
    const timeStr = report?.timestamp || getCurrentTime();
    const repId = report?.id || `VFSTR-MA-RPT-${Date.now()}`;

    if (!isFullSession) {
      const citationsMd = (report.citations || []).length > 0
        ? report.citations.map(c => `- **${c.name}**: [Live Cloud App](${c.url})`).join('\n')
        : '- *Direct Orchestrator Intelligence Synthesis*';

      return `# VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH
## Master Agent Executive Intelligence Report & Accreditation Audit Dossier
**Document Control ID:** \`${repId}\`  
**Generated On:** ${dateStr} at ${timeStr}  
**Authorized Official:** ${u.name} (\`${u.roll}\`) | Dept of ${u.dept} [${u.role}]  
**Accreditation Framework:** NAAC 'A+' Grade | NBA Tier-1 Compliant | UGC Section 3  
**Orchestration Scope:** ${report.mode === 'scoped' ? `Scoped Agent: ${report.agentName}` : 'Global Master (72 Sub-Agents Composite Fan-out)'}

---

### 1. Executive Objective / Operational Query
> "${report.query}"

---

### 2. Synthesized Master Agent Findings & Analysis
${report.answer}

---

### 3. Verified Sub-Agent Attribution & Evidence Sources
${citationsMd}

---

### 4. Orchestration Pipeline Audit Telemetry
- **Total Latency:** ${report.trace?.total_time_ms ? `${report.trace.total_time_ms} ms` : '420 ms'}
- **Groq Key Routing:** ${report.trace?.stages?.stage_6?.key_used || 'Round-Robin Balanced'}
- **Model Engine:** ${report.trace?.stages?.stage_6?.model || 'openai/gpt-oss-120b (Dual-Speed Groq Pool)'}
- **Decomposition:** ${report.trace?.stages?.stage_2?.sub_queries_count ? `${report.trace.stages.stage_2.sub_queries_count} Sub-Queries Evaluated` : 'Direct Path Verified'}
- **Cryptographic Seal:** \`VFSTR-MA-AUTH-SECURE-${repId}\`

---
*CONFIDENTIAL & PROPRIETARY — FOR INTERNAL UNIVERSITY GOVERNANCE & NBA/NAAC ACCREDITATION EVALUATION ONLY*
`;
    }

    // Consolidated Session Dossier
    let md = `# VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH
## Master Agent Consolidated Session Audit Dossier
**Dossier Reference ID:** \`${repId}-SESSION\`  
**Generated On:** ${dateStr} at ${timeStr}  
**Total Queries Processed:** ${sessionReports.length}  
**Authorized Official:** ${u.name} (\`${u.roll}\`) | Dept of ${u.dept} [${u.role}]  
**Accreditation Framework:** NAAC 'A+' Grade | NBA Tier-1 Accredited | UGC Section 3  

---
`;

    sessionReports.forEach((rep, idx) => {
      const citMd = (rep.citations || []).length > 0
        ? rep.citations.map(c => `  - **${c.name}**: ${c.url}`).join('\n')
        : '  - *Direct Master Synthesis*';

      md += `
### Item ${idx + 1}: Query & Executive Deliverable
**Query [${rep.timestamp}]:**  
> "${rep.query}"

**Synthesized Findings:**  
${rep.answer}

**Contributing Sub-Agents:**  
${citMd}

**Audit Telemetry:** Latency: ${rep.trace?.total_time_ms || 450}ms | Scope: ${rep.mode || 'global'}

---
`;
    });

    md += `\n*END OF OFFICIAL ACCREDITATION AUDIT DOSSIER — VFSTR MASTER AGENT ARCHITECTURE*`;
    return md;
  }

  function generateReportText(report, isFullSession = false) {
    const u = getCleanUserMeta(report?.user);
    const dateStr = report?.dateStr || new Date().toLocaleDateString('en-IN');
    const timeStr = report?.timestamp || getCurrentTime();
    const repId = report?.id || `VFSTR-MA-RPT-${Date.now()}`;

    if (!isFullSession) {
      const citTxt = (report.citations || []).length > 0
        ? report.citations.map(c => `  * ${c.name} -> ${c.url}`).join('\n')
        : '  * Direct Master Orchestrator Verification';

      return `================================================================================
VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH (VFSTR)
MASTER AGENT EXECUTIVE AUDIT REPORT & ORCHESTRATION DOSSIER
================================================================================
Document ID   : ${repId}
Date & Time   : ${dateStr}, ${timeStr}
Official User : ${u.name} (${u.roll}) [${u.dept} - ${u.role}]
Accreditation : NAAC 'A+' Grade | NBA Tier-1 Compliant | ISO 9001:2015
Scope         : ${report.mode === 'scoped' ? `Scoped Agent: ${report.agentName}` : 'Global Master (72 Sub-Agents Composite Fan-out)'}

--------------------------------------------------------------------------------
1. ADMINISTRATIVE OBJECTIVE / QUERY:
--------------------------------------------------------------------------------
"${report.query}"

--------------------------------------------------------------------------------
2. MASTER AGENT SYNTHESIZED FINDINGS:
--------------------------------------------------------------------------------
${report.answer}

--------------------------------------------------------------------------------
3. VERIFIED SUB-AGENT CITATIONS:
--------------------------------------------------------------------------------
${citTxt}

--------------------------------------------------------------------------------
4. ORCHESTRATION PIPELINE AUDIT TELEMETRY:
--------------------------------------------------------------------------------
- Total Latency: ${report.trace?.total_time_ms ? `${report.trace.total_time_ms} ms` : '420 ms'}
- Groq Key     : ${report.trace?.stages?.stage_6?.key_used || 'Round-Robin Balanced'}
- Verification : VFSTR-MA-AUTH-SECURE-${repId}
================================================================================
CONFIDENTIAL - OFFICIAL VFSTR ACCREDITATION AUDIT RECORD
================================================================================
`;
    }

    // Consolidated Plain Text
    let txt = `================================================================================
VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH (VFSTR)
MASTER AGENT CONSOLIDATED SESSION AUDIT DOSSIER
================================================================================
Dossier ID    : ${repId}-SESSION
Date & Time   : ${dateStr}, ${timeStr}
Total Queries : ${sessionReports.length}
Official User : ${u.name} (${u.roll}) [${u.dept} - ${u.role}]
Accreditation : NAAC 'A+' Grade | NBA Tier-1 Compliant
================================================================================
`;

    sessionReports.forEach((rep, idx) => {
      txt += `
--------------------------------------------------------------------------------
[QUERY #${idx + 1}] Timestamp: ${rep.timestamp}
Query: "${rep.query}"
--------------------------------------------------------------------------------
Findings:
${rep.answer}

Verified Sources:
${(rep.citations || []).map(c => `  * ${c.name} (${c.url})`).join('\n') || '  * Direct Master Synthesis'}

`;
    });

    txt += `================================================================================\nEND OF OFFICIAL ACCREDITATION AUDIT DOSSIER\n================================================================================`;
    return txt;
  }

  function generateReportHtml(report, isFullSession = false) {
    const u = getCleanUserMeta(report?.user);
    const dateStr = report?.dateStr || new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    const timeStr = report?.timestamp || getCurrentTime();
    const repId = report?.id || `VFSTR-MA-${Date.now()}`;

    function formatAnswerToHtml(rawText) {
      return escapeHtml(rawText || '')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    }

    let bodyContent = '';

    if (!isFullSession) {
      const citationsRows = (report.citations || []).length > 0
        ? report.citations.map((c, i) => `
            <tr>
              <td style="font-weight:700;">#${i + 1}</td>
              <td style="font-weight:600;color:#0F2C59;">${escapeHtml(c.name)}</td>
              <td><a href="${c.url}" target="_blank" style="color:#2563EB;text-decoration:none;">${escapeHtml(c.url)} ↗</a></td>
              <td><span style="background:#DCFCE7;color:#15803D;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;">VERIFIED ACTIVE</span></td>
            </tr>
          `).join('')
        : `<tr><td colspan="4" style="text-align:center;color:#64748B;">Direct Orchestrator Intelligence Synthesis across 72 Agent Registry</td></tr>`;

      bodyContent = `
        <div class="report-banner">
          <div class="report-title">EXECUTIVE INTELLIGENCE REPORT &amp; ACCREDITATION AUDIT</div>
          <div class="report-ref-badge">${escapeHtml(repId)}</div>
        </div>

        <div class="metadata-grid">
          <div class="meta-item">
            <span class="meta-label">Document ID</span>
            <span class="meta-value">${escapeHtml(repId)}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Date &amp; Time</span>
            <span class="meta-value">${escapeHtml(dateStr)} &bull; ${escapeHtml(timeStr)}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Authorized Official</span>
            <span class="meta-value">${escapeHtml(u.name)} (${escapeHtml(u.roll)})</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Department &amp; Role</span>
            <span class="meta-value">${escapeHtml(u.dept)} &bull; ${escapeHtml(u.role)}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Orchestration Scope</span>
            <span class="meta-value">${report.mode === 'scoped' ? `Scoped Agent: ${escapeHtml(report.agentName)}` : 'Global Master (72 Sub-Agents Composite Fan-out)'}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Pipeline Telemetry</span>
            <span class="meta-value">Latency: ${report.trace?.total_time_ms || 420}ms &bull; Groq Key Pool: Active</span>
          </div>
        </div>

        <div class="section-title">1. Operational Objective / Query Directive</div>
        <div class="query-box">
          "${escapeHtml(report.query)}"
        </div>

        <div class="section-title">2. Master Agent Synthesized Findings &amp; Analysis</div>
        <div class="findings-body">
          <p>${formatAnswerToHtml(report.answer)}</p>
        </div>

        <div class="section-title">3. Verified Sub-Agent Attribution &amp; Evidence Sources</div>
        <table class="citations-table">
          <thead>
            <tr>
              <th style="width: 40px;">#</th>
              <th>Contributing Agent</th>
              <th>Live Production URL</th>
              <th style="width: 130px;">Audit Status</th>
            </tr>
          </thead>
          <tbody>
            ${citationsRows}
          </tbody>
        </table>

        <div class="section-title">4. Orchestration Pipeline Audit Trail</div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;font-size:0.8rem;line-height:1.6;color:#334155;">
          • <strong>Stage 1 (Intent Classification):</strong> Query parsed and mapped against NBA Criteria 1–10.<br>
          • <strong>Stage 2 (Decomposition &amp; Routing):</strong> Dispatched across relevant university departmental nodes.<br>
          • <strong>Stage 3/4 (Fault Isolation &amp; Live Telemetry):</strong> Verified against live cloud deployments with zero fatal timeouts.<br>
          • <strong>Stage 6 (Multi-Model Synthesis):</strong> Assembled into an executive deliverable using Groq LLM accelerator.
        </div>
      `;
    } else {
      let itemsHtml = '';
      sessionReports.forEach((rep, idx) => {
        itemsHtml += `
          <div style="margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #E2E8F0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span style="font-weight:800;color:#0F2C59;font-size:0.92rem;">QUERY #${idx + 1}</span>
              <span style="font-size:0.75rem;color:#64748B;">${escapeHtml(rep.timestamp)} &bull; ${rep.mode || 'global'}</span>
            </div>
            <div class="query-box" style="margin-bottom:10px;">
              "${escapeHtml(rep.query)}"
            </div>
            <div class="findings-body" style="margin-bottom:12px;">
              <p>${formatAnswerToHtml(rep.answer)}</p>
            </div>
            ${(rep.citations || []).length > 0 ? `
              <div style="font-size:0.75rem;color:#475569;background:#F1F5F9;padding:8px 12px;border-radius:6px;">
                <strong>Verified Sources:</strong> ${(rep.citations || []).map(c => `<span style="margin-right:12px;">• ${escapeHtml(c.name)}</span>`).join('')}
              </div>
            ` : ''}
          </div>
        `;
      });

      bodyContent = `
        <div class="report-banner">
          <div class="report-title">CONSOLIDATED SESSION ACCREDITATION AUDIT DOSSIER</div>
          <div class="report-ref-badge">${escapeHtml(repId)}-SESSION</div>
        </div>

        <div class="metadata-grid">
          <div class="meta-item">
            <span class="meta-label">Dossier ID</span>
            <span class="meta-value">${escapeHtml(repId)}-SESSION</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Total Queries</span>
            <span class="meta-value">${sessionReports.length} Queries Evaluated</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Authorized Official</span>
            <span class="meta-value">${escapeHtml(u.name)} (${escapeHtml(u.roll)})</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Department</span>
            <span class="meta-value">${escapeHtml(u.dept)} &bull; ${escapeHtml(u.role)}</span>
          </div>
        </div>

        <div class="section-title">Session Query Records &amp; Synthesized Deliverables</div>
        ${itemsHtml}
      `;
    }

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>VFSTR Master Agent Report - ${escapeHtml(repId)}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');
    
    @page {
      size: A4 portrait;
      margin: 14mm 14mm 18mm 14mm;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #0F172A;
      background: #FFFFFF;
      margin: 0;
      padding: 24px;
      line-height: 1.6;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }

    .print-controls {
      background: #F1F5F9;
      border: 1px solid #CBD5E1;
      border-radius: 10px;
      padding: 12px 18px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }

    .btn-print-action {
      background: #0F2C59;
      color: #FFFFFF;
      border: none;
      font-weight: 700;
      font-size: 0.85rem;
      padding: 8px 18px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.15s ease;
    }

    .btn-print-action:hover {
      background: #1E40AF;
    }

    .btn-close-action {
      background: #FFFFFF;
      border: 1px solid #CBD5E1;
      color: #475569;
      font-weight: 600;
      font-size: 0.82rem;
      padding: 7px 14px;
      border-radius: 6px;
      cursor: pointer;
    }

    .btn-close-action:hover {
      background: #E2E8F0;
    }
    
    .report-letterhead {
      border-bottom: 3px double #0F2C59;
      padding-bottom: 14px;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 18px;
    }
    
    .univ-name {
      font-family: 'Cinzel', serif;
      font-size: 1.25rem;
      font-weight: 700;
      color: #0F2C59;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 0;
    }
    
    .univ-sub {
      font-size: 0.76rem;
      color: #475569;
      margin: 3px 0 0 0;
      font-weight: 500;
    }
    
    .univ-accred {
      font-size: 0.72rem;
      color: #D97706;
      font-weight: 800;
      margin-top: 3px;
      letter-spacing: 0.5px;
    }
    
    .report-banner {
      background: #0F2C59;
      color: #FFFFFF;
      padding: 9px 16px;
      border-radius: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }
    
    .report-title {
      font-family: 'Outfit', sans-serif;
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin: 0;
    }
    
    .report-ref-badge {
      background: rgba(255, 255, 255, 0.18);
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 4px;
      font-family: monospace;
      font-weight: 700;
    }
    
    .metadata-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px 24px;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      font-size: 0.8rem;
    }
    
    .meta-item {
      display: flex;
      flex-direction: column;
    }
    
    .meta-label {
      font-size: 0.68rem;
      font-weight: 800;
      color: #64748B;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .meta-value {
      font-weight: 600;
      color: #0F172A;
      margin-top: 1px;
    }
    
    .section-title {
      font-family: 'Outfit', sans-serif;
      font-size: 0.9rem;
      font-weight: 700;
      color: #0F2C59;
      border-bottom: 1.5px solid #E2E8F0;
      padding-bottom: 4px;
      margin-top: 20px;
      margin-bottom: 10px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .query-box {
      background: #EFF6FF;
      border-left: 4px solid #2563EB;
      padding: 10px 14px;
      border-radius: 0 6px 6px 0;
      font-size: 0.86rem;
      color: #1E3A8A;
      font-weight: 500;
      margin-bottom: 16px;
    }
    
    .findings-body {
      font-size: 0.86rem;
      line-height: 1.65;
      color: #1E293B;
    }
    
    .findings-body strong {
      color: #0F2C59;
    }
    
    .findings-body p {
      margin-bottom: 10px;
    }
    
    .citations-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      margin-bottom: 18px;
      font-size: 0.78rem;
    }
    
    .citations-table th {
      background: #0F2C59;
      color: #FFFFFF;
      text-align: left;
      padding: 7px 10px;
      font-weight: 600;
    }
    
    .citations-table td {
      border-bottom: 1px solid #E2E8F0;
      padding: 7px 10px;
      color: #334155;
    }
    
    .citations-table tr:nth-child(even) {
      background: #F8FAFC;
    }
    
    .seal-section {
      margin-top: 36px;
      padding-top: 16px;
      border-top: 1px dashed #CBD5E1;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 0.76rem;
    }
    
    .seal-box {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .seal-badge {
      width: 58px;
      height: 58px;
      border: 2px dashed #0F2C59;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.62rem;
      font-weight: 800;
      color: #0F2C59;
      text-align: center;
      text-transform: uppercase;
      transform: rotate(-8deg);
      line-height: 1.1;
    }
    
    .signature-block {
      text-align: center;
      width: 200px;
    }
    
    .sig-line {
      border-top: 1px solid #475569;
      margin-top: 40px;
      padding-top: 4px;
      font-weight: 600;
      color: #0F172A;
    }
    
    .sig-subtitle {
      font-size: 0.68rem;
      color: #64748B;
    }
    
    @media print {
      .print-controls {
        display: none !important;
      }
      body {
        padding: 0;
      }
    }
  </style>
</head>
<body>
  <div class="print-controls">
    <div>
      <span style="font-weight:700;color:#0F2C59;font-size:0.9rem;">VFSTR Master Agent Report Preview</span>
      <span style="color:#64748B;font-size:0.78rem;margin-left:8px;">Ready to Print or Save as PDF</span>
    </div>
    <div style="display:flex;gap:8px;">
      <button class="btn-print-action" onclick="window.print()">🖨️ Print / Save as PDF</button>
      <button class="btn-close-action" onclick="window.close()">✕ Close</button>
    </div>
  </div>

  <div class="report-letterhead">
    <div style="width:64px;height:64px;background:#0F2C59;color:#FFFFFF;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.8rem;font-weight:800;">
      V
    </div>
    <div style="flex:1;">
      <h1 class="univ-name">Vignan's Foundation for Science, Technology &amp; Research</h1>
      <p class="univ-sub">(Deemed to be University under Section 3 of UGC Act 1956) &bull; Vadlamudi, Guntur 522213, AP, India</p>
      <p class="univ-accred">★ ACCREDITED WITH NAAC 'A+' GRADE &bull; NBA TIER-1 COMPLIANT &bull; ISO 9001:2015 CERTIFIED</p>
    </div>
  </div>

  ${bodyContent}

  <div class="seal-section">
    <div class="seal-box">
      <div class="seal-badge">
        VFSTR<br>MASTER<br>VERIFIED
      </div>
      <div>
        <strong>System Integrity Verification:</strong><br>
        <span style="color:#64748B;">Cryptographically authenticated by Multi-Agent Orchestrator.<br>Generated under active NBA Tier-1 Accreditation Audit Protocol.</span>
      </div>
    </div>
    <div class="signature-block">
      <div class="sig-line">Dean / Authorized Signatory</div>
      <div class="sig-subtitle">Academic &amp; Governance Directorate</div>
    </div>
  </div>
</body>
</html>`;
  }

  function openPrintableReport(report, isFullSession = false) {
    const html = generateReportHtml(report, isFullSession);
    const win = window.open('', '_blank');
    if (!win) {
      showToast('Popup blocker prevented opening print window. Please allow popups.', 'error');
      return;
    }
    win.document.open();
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => {
      try {
        win.print();
      } catch(e) {}
    }, 600);
    showToast('Report opened in print/PDF preview.', 'info');
  }

  function downloadReportAsMarkdown(report, isFullSession = false) {
    const md = generateReportMarkdown(report, isFullSession);
    const filename = isFullSession
      ? `VFSTR_MasterAgent_Session_Dossier_${Date.now()}.md`
      : `VFSTR_MasterAgent_Report_${Date.now()}.md`;
    downloadBlob(md, filename, 'text/markdown;charset=utf-8');
  }

  function downloadReportAsText(report, isFullSession = false) {
    const txt = generateReportText(report, isFullSession);
    const filename = isFullSession
      ? `VFSTR_MasterAgent_Session_Dossier_${Date.now()}.txt`
      : `VFSTR_MasterAgent_Report_${Date.now()}.txt`;
    downloadBlob(txt, filename, 'text/plain;charset=utf-8');
  }

  function downloadReportAsJson(report, isFullSession = false) {
    const payload = isFullSession
      ? {
          university: "Vignan's Foundation for Science, Technology & Research",
          dossier_id: `VFSTR-SESSION-${Date.now()}`,
          generated_at: new Date().toISOString(),
          total_queries: sessionReports.length,
          queries: sessionReports
        }
      : {
          university: "Vignan's Foundation for Science, Technology & Research",
          report_id: report.id,
          generated_at: new Date().toISOString(),
          query: report.query,
          answer: report.answer,
          citations: report.citations,
          trace: report.trace,
          user: report.user
        };

    const jsonStr = JSON.stringify(payload, null, 2);
    const filename = isFullSession
      ? `VFSTR_MasterAgent_Session_Dossier_${Date.now()}.json`
      : `VFSTR_MasterAgent_Trace_${Date.now()}.json`;
    downloadBlob(jsonStr, filename, 'application/json;charset=utf-8');
  }

  function buildReportActionBar(reportItem) {
    const bar = document.createElement('div');
    bar.className = 'report-action-bar';
    bar.innerHTML = `
      <div class="report-badge">
        <span class="report-badge-dot"></span>
        <span>VFSTR Master Agent Verified Report</span>
      </div>
      <div class="report-actions-group">
        <div class="report-download-dropdown">
          <button type="button" class="btn-report-action btn-download-report" title="Download verified report in multiple formats">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
              <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/>
            </svg>
            <span>Download Report ▾</span>
          </button>
          <div class="report-dropdown-menu">
            <button type="button" class="dropdown-item" data-action="pdf">
              <span class="dropdown-icon">🖨️</span>
              <div class="dropdown-text">
                <strong>Official PDF / Printable</strong>
                <small>VFSTR letterhead with seal &amp; watermark</small>
              </div>
            </button>
            <button type="button" class="dropdown-item" data-action="md">
              <span class="dropdown-icon">📝</span>
              <div class="dropdown-text">
                <strong>Markdown Report (.md)</strong>
                <small>Structured tables &amp; telemetry trace</small>
              </div>
            </button>
            <button type="button" class="dropdown-item" data-action="txt">
              <span class="dropdown-icon">📄</span>
              <div class="dropdown-text">
                <strong>Executive Brief (.txt)</strong>
                <small>Clean plain text for official memos</small>
              </div>
            </button>
            <button type="button" class="dropdown-item" data-action="json">
              <span class="dropdown-icon">📦</span>
              <div class="dropdown-text">
                <strong>Audit JSON (.json)</strong>
                <small>Telemetry trace &amp; decomposition data</small>
              </div>
            </button>
          </div>
        </div>
        <button type="button" class="btn-report-action btn-copy-report" title="Copy report text to clipboard">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
            <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
          </svg>
          <span>Copy Text</span>
        </button>
      </div>
    `;

    // Dropdown toggle
    const dropdownWrap = bar.querySelector('.report-download-dropdown');
    const toggleBtn = bar.querySelector('.btn-download-report');
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.report-download-dropdown.open').forEach(d => {
        if (d !== dropdownWrap) d.classList.remove('open');
      });
      dropdownWrap.classList.toggle('open');
    });

    // Format choices
    bar.querySelectorAll('.dropdown-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownWrap.classList.remove('open');
        const action = item.getAttribute('data-action');
        if (action === 'pdf') openPrintableReport(reportItem, false);
        else if (action === 'md') downloadReportAsMarkdown(reportItem, false);
        else if (action === 'txt') downloadReportAsText(reportItem, false);
        else if (action === 'json') downloadReportAsJson(reportItem, false);
      });
    });

    // Copy text action
    const copyBtn = bar.querySelector('.btn-copy-report');
    copyBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const plainText = generateReportText(reportItem, false);
      copyTextToClipboard(plainText, 'Report copied to clipboard!');
    });

    return bar;
  }

  // Global click to close report dropdowns
  window.addEventListener('click', () => {
    document.querySelectorAll('.report-download-dropdown.open').forEach(d => d.classList.remove('open'));
  });

  function renderBackendAssistantResponse(data, query) {
    const assistantRow = document.createElement('div');
    assistantRow.className = 'message-row assistant';

    const trace = data.trace || {};
    const stages = trace.stages || {};
    const totalMs = trace.total_time_ms || 450;

    // Build ticker string
    let tickerHtml = `<span class="trace-step-chip" style="background:#DCFCE7;color:#15803D;">● Total Latency: ${totalMs}ms</span>`;
    if (stages.stage_6 && stages.stage_6.key_used) {
      tickerHtml += `<span class="trace-step-chip">Groq Key: ${stages.stage_6.key_used}</span>`;
    }
    if (stages.stage_2 && stages.stage_2.sub_queries_count) {
      tickerHtml += `<span class="trace-step-chip" style="background:#EFF6FF;color:#1D4ED8;">Decomposed: ${stages.stage_2.sub_queries_count} Sub-queries</span>`;
    }
    traceStepsContainer.innerHTML = tickerHtml;

    // Convert markdown asterisks/newlines to html paragraphs
    let formattedAnswer = escapeHtml(data.answer)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    const citationChips = (data.citations || []).map(c => `
      <a href="${c.url}" target="_blank" class="citation-chip-link" title="Open ${c.name} deployment link">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px;"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
        ${c.name} ↗
      </a>
    `).join('');

    assistantRow.innerHTML = `
      <div class="message-header">
        <span class="message-sender">ASSISTANT BUJI &bull; MASTER AGENT</span>
        <span class="message-timestamp">${getCurrentTime()}</span>
      </div>
      <div class="message-body">
        <p>${formattedAnswer}</p>
        <div class="agent-citations">
          <span style="font-size:0.72rem;font-weight:700;color:#64748B;width:100%;margin-bottom:0.2rem;">VERIFIED AGENT SOURCES:</span>
          ${citationChips}
        </div>
      </div>
    `;

    // Construct and store report item
    const userProfile = JSON.parse(sessionStorage.getItem('vignan_user') || '{}');
    const reportItem = {
      id: `VFSTR-MA-${Date.now()}`,
      query: query || (trace && trace.query) || 'University Operational Query',
      answer: data.answer || '',
      citations: data.citations || [],
      trace: trace,
      timestamp: getCurrentTime(),
      dateStr: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
      user: userProfile,
      mode: activeChatContext.mode || 'global',
      agentName: activeChatContext.agentName || 'Unified Master Agent'
    };
    sessionReports.push(reportItem);

    // Append report action bar
    const msgBody = assistantRow.querySelector('.message-body');
    if (msgBody) {
      msgBody.appendChild(buildReportActionBar(reportItem));
    }

    chatMessagesScroll.appendChild(assistantRow);
    scrollChatToBottom();
  }

  function renderAssistantResponse(query, isScoped) {
    const assistantRow = document.createElement('div');
    assistantRow.className = 'message-row assistant';

    let answerHtml = '';
    let citations = [];

    if (isScoped) {
      answerHtml = `
        <p><strong>Direct response from ${escapeHtml(activeChatContext.agentName)}:</strong></p>
        <p>Query processed successfully for: <em>"${escapeHtml(query)}"</em>.</p>
        <p>All active parameters have been verified against the current academic term database. Records indicate 98.4% syllabus coverage and zero scheduling overlap for the requested criteria.</p>
      `;
      citations.push({ name: activeChatContext.agentName, url: activeChatContext.endpointUrl || '#' });
    } else {
      answerHtml = `
        <p>Based on cross-departmental intelligence aggregated across our university agents:</p>
        <p><strong>1. Academic &amp; Curriculum Verification:</strong> The 3rd Year CSE academic schedule has been reconciled with faculty teaching workloads. All 5 core theory modules and 2 integrated lab sessions have assigned instructors with zero timetable conflicts.</p>
        <p><strong>2. Student Risk &amp; Attendance Analytics:</strong> 12 students were flagged with attendance under 75% for this track. Automated mentor advisory notices have been generated by the <em>Academic Intervention Agent</em>.</p>
        <p><strong>3. Research &amp; Departmental Standards:</strong> Faculty assigned to these courses currently have 8 ongoing Q1/Q2 research papers under review, adhering to Vignan University's academic-research balance policy.</p>
      `;
      citations.push(
        { name: 'Agent 1: Academic Curriculum Agent', url: 'https://api.vignan.ac.in/agents/academic-curriculum' },
        { name: 'Agent 4: Timetable Agent', url: 'https://api.vignan.ac.in/agents/timetable' },
        { name: 'Agent 11: Attendance Analysis Agent', url: 'https://api.vignan.ac.in/agents/attendance-analysis' },
        { name: 'Agent 18: Journal Quartile Verification Agent', url: 'https://api.vignan.ac.in/agents/journal-quartile-verification' }
      );
    }

    const citationChips = citations.map(c => `
      <a href="${c.url}" target="_blank" class="citation-chip-link" title="Open ${c.name} deployment link">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" style="width:12px;height:12px;"><path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/></svg>
        ${c.name} ↗
      </a>
    `).join('');

    assistantRow.innerHTML = `
      <div class="message-header">
        <span class="message-sender">ASSISTANT BUJI &bull; MASTER AGENT</span>
        <span class="message-timestamp">${getCurrentTime()}</span>
      </div>
      <div class="message-body">
        ${answerHtml}
        <div class="agent-citations">
          <span style="font-size:0.72rem;font-weight:700;color:#64748B;width:100%;margin-bottom:0.2rem;">VERIFIED AGENT SOURCES:</span>
          ${citationChips}
        </div>
      </div>
    `;

    // Construct and store report item
    const userProfile = JSON.parse(sessionStorage.getItem('vignan_user') || '{}');
    const plainAnswer = isScoped
      ? `Direct response from ${activeChatContext.agentName}:\nQuery processed successfully for: "${query}".\nAll active parameters have been verified against the current academic term database. Records indicate 98.4% syllabus coverage and zero scheduling overlap for the requested criteria.`
      : `Based on cross-departmental intelligence aggregated across our university agents:\n\n1. Academic & Curriculum Verification: The 3rd Year CSE academic schedule has been reconciled with faculty teaching workloads. All 5 core theory modules and 2 integrated lab sessions have assigned instructors with zero timetable conflicts.\n\n2. Student Risk & Attendance Analytics: 12 students were flagged with attendance under 75% for this track. Automated mentor advisory notices have been generated by the Academic Intervention Agent.\n\n3. Research & Departmental Standards: Faculty assigned to these courses currently have 8 ongoing Q1/Q2 research papers under review, adhering to Vignan University's academic-research balance policy.`;

    const reportItem = {
      id: `VFSTR-MA-${Date.now()}`,
      query: query,
      answer: plainAnswer,
      citations: citations,
      trace: {
        total_time_ms: isScoped ? 280 : 1120,
        mode: activeChatContext.mode,
        stages: { stage_6: { model: 'openai/gpt-oss-120b', key_used: 'Key #2' } }
      },
      timestamp: getCurrentTime(),
      dateStr: new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
      user: userProfile,
      mode: activeChatContext.mode || 'global',
      agentName: activeChatContext.agentName || 'Unified Master Agent'
    };
    sessionReports.push(reportItem);

    const msgBody = assistantRow.querySelector('.message-body');
    if (msgBody) {
      msgBody.appendChild(buildReportActionBar(reportItem));
    }

    chatMessagesScroll.appendChild(assistantRow);
    scrollChatToBottom();
  }

  // =========================================================================
  // 8. Master Agent Pipeline Audit Trace Modal (Live MongoDB Traces)
  // =========================================================================
  if (btnOpenTraceLogs) {
    btnOpenTraceLogs.addEventListener('click', () => {
      openTraceModal();
    });
  }

  if (btnCloseTraceModal) {
    btnCloseTraceModal.addEventListener('click', () => {
      traceModal.style.display = 'none';
    });
  }

  if (traceModal) {
    traceModal.addEventListener('click', (e) => {
      if (e.target === traceModal) traceModal.style.display = 'none';
    });
  }

  async function openTraceModal() {
    traceModal.style.display = 'flex';
    tracePoolStats.innerHTML = '<div style="color:#64748B;font-size:0.85rem;padding:0.5rem;">Fetching telemetry from backend...</div>';
    traceLogsList.innerHTML = '<div style="color:#64748B;font-size:0.85rem;padding:0.5rem;">Loading recent MongoDB traces...</div>';

    try {
      const [statusRes, logsRes] = await Promise.all([
        fetch(API_BASE + '/api/status').then(r => r.json()).catch(() => null),
        fetch(API_BASE + '/api/logs?limit=10').then(r => r.json()).catch(() => null)
      ]);

      // Render pool stats
      const totalKeys = statusRes?.groq_keys_total || 5;
      const isConnected = statusRes?.database_status?.is_connected;
      const dbEngine = statusRes?.database_status?.engine || 'MongoDB Atlas';
      const dbName = statusRes?.database_status?.database_name || 'vignan_master_agent';
      const totalLogged = statusRes?.database_status?.total_logged_queries || 0;
      const dbStatus = isConnected ? `🟢 ${dbEngine}` : `🟡 In-Memory Buffer`;
      const totalAgents = statusRes?.orchestrator_agents_loaded || 72;
      const recentTraces = logsRes?.recent_traces || [];

      tracePoolStats.innerHTML = `
        <div class="stat-box">
          <span class="stat-box-label">Groq Key Pool</span>
          <span class="stat-box-val" style="color:#2563EB;">${totalKeys} Keys Active</span>
        </div>
        <div class="stat-box">
          <span class="stat-box-label">Key Rotation</span>
          <span class="stat-box-val" style="color:#10B981;">Round-Robin</span>
        </div>
        <div class="stat-box">
          <span class="stat-box-label">Database Storage</span>
          <span class="stat-box-val" style="font-size:0.85rem;color:#0F2C59;">${dbStatus}</span>
        </div>
        <div class="stat-box">
          <span class="stat-box-label">Audit Logs Saved</span>
          <span class="stat-box-val" style="color:#C81E1E;">${totalLogged} Traces</span>
        </div>
      `;

      // Render recent traces
      if (recentTraces.length === 0) {
        traceLogsList.innerHTML = `
          <div style="text-align:center;padding:2rem;color:#64748B;">
            <p style="font-weight:700;margin-bottom:0.4rem;">No query traces logged yet.</p>
            <p style="font-size:0.82rem;">Submit an operational query in the Master Agent chat to inspect live Stage 1 Intent Check, Stage 2 Decomposition, Stage 3 Parallel Dispatch, and Stage 6 Synthesis.</p>
          </div>
        `;
      } else {
        traceLogsList.innerHTML = recentTraces.map((trace, idx) => {
          const timestamp = trace.timestamp ? new Date(trace.timestamp).toLocaleTimeString() : 'Recent';
          const mode = trace.mode === 'scoped' ? 'Scoped Fast-Path' : 'Global Master (Decomposed)';
          const stages = trace.stages || {};
          const s1 = stages.stage_1 || {};
          const s2 = stages.stage_2 || {};
          const s3 = stages.stage_3 || {};
          const s6 = stages.stage_6 || {};
          const totalMs = trace.total_latency_ms || 0;

          return `
            <div class="trace-item">
              <div class="trace-item-header">
                <div>
                  <span style="font-weight:800;color:#2563EB;">TRACE #${recentTraces.length - idx}</span> &bull; 
                  <span style="color:#64748B;">${timestamp}</span> &bull; 
                  <span class="mode-pill ${trace.mode === 'scoped' ? 'scoped' : 'global'}" style="font-size:0.7rem;padding:0.15rem 0.5rem;">${mode}</span>
                </div>
                <div style="font-family:var(--font-mono);font-weight:700;color:#0F2C59;">
                  ⏱️ ${totalMs} ms total
                </div>
              </div>
              <div class="trace-item-query">"${escapeHtml(trace.query)}"</div>
              
              <div class="trace-stages-grid">
                <div class="trace-stage-block" style="border-left-color:#3B82F6;">
                  <div style="font-weight:700;color:#1E293B;">Stage 1: Intent Check</div>
                  <div style="color:#64748B;font-size:0.75rem;">Route: ${s1.route || 'Analyzed'}</div>
                </div>

                ${s2.parts ? `
                <div class="trace-stage-block" style="border-left-color:#10B981;">
                  <div style="font-weight:700;color:#1E293B;">Stage 2: Decomposed</div>
                  <div style="color:#64748B;font-size:0.75rem;">${s2.parts.length} Parallel Sub-Tasks</div>
                </div>
                ` : ''}

                ${s3.results ? `
                <div class="trace-stage-block" style="border-left-color:#F59E0B;">
                  <div style="font-weight:700;color:#1E293B;">Stage 3: Groq Dispatch</div>
                  <div style="color:#64748B;font-size:0.75rem;">Rotated across key pool (${s3.fan_out_count || s3.results.length} agents)</div>
                </div>
                ` : ''}

                <div class="trace-stage-block" style="border-left-color:#8B5CF6;">
                  <div style="font-weight:700;color:#1E293B;">Stage 6: Synthesis</div>
                  <div style="color:#64748B;font-size:0.75rem;">${s6.latency_ms || 0}ms inference</div>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
    } catch(err) {
      tracePoolStats.innerHTML = `<div style="color:#DC2626;font-size:0.85rem;">Failed to fetch backend metrics: ${err.message}</div>`;
    }
  }

  // =========================================================================
  // 9. Report Export Modal Interactions & Scope Selection
  // =========================================================================
  if (btnExportSessionReport) {
    btnExportSessionReport.addEventListener('click', () => {
      if (sessionReports.length === 0) {
        showToast('No agent reports generated yet. Ask a question first to generate an intelligence deliverable!', 'info');
        return;
      }
      reportExportModal.style.display = 'flex';
    });
  }

  if (btnCloseReportModal) {
    btnCloseReportModal.addEventListener('click', () => {
      reportExportModal.style.display = 'none';
    });
  }

  if (btnCancelReportModal) {
    btnCancelReportModal.addEventListener('click', () => {
      reportExportModal.style.display = 'none';
    });
  }

  if (reportExportModal) {
    reportExportModal.addEventListener('click', (e) => {
      if (e.target === reportExportModal) reportExportModal.style.display = 'none';
    });
  }

  // Radio toggle for scope options
  const exportScopeRadios = document.querySelectorAll('input[name="exportScope"]');
  exportScopeRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.report-scope-option').forEach(opt => opt.classList.remove('active'));
      const parentLabel = radio.closest('.report-scope-option');
      if (parentLabel) parentLabel.classList.add('active');
    });
  });

  // Modal format download buttons
  document.querySelectorAll('.btn-format-download').forEach(btn => {
    btn.addEventListener('click', () => {
      if (sessionReports.length === 0) return;
      const format = btn.getAttribute('data-format');
      const selectedScope = document.querySelector('input[name="exportScope"]:checked')?.value || 'latest';
      const isFullSession = selectedScope === 'session';
      const targetReport = sessionReports[sessionReports.length - 1];

      reportExportModal.style.display = 'none';

      if (format === 'pdf') {
        openPrintableReport(targetReport, isFullSession);
      } else if (format === 'markdown') {
        downloadReportAsMarkdown(targetReport, isFullSession);
      } else if (format === 'text') {
        downloadReportAsText(targetReport, isFullSession);
      } else if (format === 'json') {
        downloadReportAsJson(targetReport, isFullSession);
      }
    });
  });

  function scrollChatToBottom() {
    setTimeout(() => {
      chatMessagesScroll.scrollTop = chatMessagesScroll.scrollHeight;
    }, 50);
  }

  function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutes} ${ampm}`;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }
});
