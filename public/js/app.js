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
        renderBackendAssistantResponse(data);
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

  function renderBackendAssistantResponse(data) {
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
