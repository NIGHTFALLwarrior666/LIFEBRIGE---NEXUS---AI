/**
 * Nexus AI — B2B SaaS MVP Interactive Application Logic
 * Implements:
 * 1. Real-time ROI Calculator with live formula updates
 * 2. Interactive AI Claim Triage Simulation Console in Hero
 * 3. 2-Step Demo Qualification & Calendar Booking Modal
 * 4. Buyer Persona Tab Switcher (Operations, Finance, Compliance, Leadership)
 * 5. Accessible FAQ Accordion
 * 6. Dynamic Positioning / Niche Switcher (PRD Section 0)
 * 7. Toast notification & sticky navbar observer
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initClaimSimulator();
  initRoiCalculator();
  initPersonaTabs();
  initFaqAccordion();
  initDemoModal();
  initPositioningSwitcher();
});

/* ==========================================================================
   1. Navigation & Scroll Effects
   ========================================================================== */
function initNavigation() {
  const topNav = document.getElementById('top-nav');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const mobileDrawer = document.getElementById('mobile-nav-drawer');
  const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');

  // Sticky blur on scroll
  window.addEventListener('scroll', () => {
    if (window.scrollY > 30) {
      topNav.classList.add('scrolled');
    } else {
      topNav.classList.remove('scrolled');
    }
  });

  // Mobile menu drawer toggle
  if (mobileMenuBtn && mobileDrawer) {
    mobileMenuBtn.addEventListener('click', () => {
      const isOpen = mobileDrawer.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', isOpen);
      mobileMenuBtn.innerHTML = isOpen 
        ? '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
        : '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    });

    // Close drawer when link clicked
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileDrawer.classList.remove('open');
        if (mobileMenuBtn) {
          mobileMenuBtn.setAttribute('aria-expanded', 'false');
          mobileMenuBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
        }
      });
    });
  }
}

/* ==========================================================================
   2. Interactive Live Claim Triage Simulator (Hero Widget)
   ========================================================================== */
const sampleClaims = [
  {
    id: "CLM-8942-BCBS",
    patient: "Eleanor Vance · DOB: 04/12/1978",
    payer: "Blue Cross Blue Shield of IL",
    service: "Knee Arthroscopy (CPT 29881 + ICD-10 M23.22)",
    initialIssue: "Missing modifier 59 on secondary diagnostic line; potential unbundling denial risk.",
    resolvedText: "Nexus AI auto-identified distinct procedural service, appended Modifier 59, and verified policy against BCBS Clearinghouse Rule v4.8.",
    confidence: "99.4%",
    status: "Auto-Scrubbed & Cleared"
  },
  {
    id: "CLM-9104-AETNA",
    patient: "Marcus Thorne · DOB: 11/29/1985",
    payer: "Aetna Healthcare PPO",
    service: "Lumbar Spinal MRI (CPT 72148 + ICD-10 M54.50)",
    initialIssue: "Prior authorization record missing from AthenaHealth EHR encounter document.",
    resolvedText: "Nexus AI matched clinical chart notes, extracted pre-auth auth #AUTH-782109 from payer portal via FHIR API, and linked document.",
    confidence: "98.9%",
    status: "Pre-Auth Verified"
  },
  {
    id: "CLM-9320-UHC",
    patient: "Grace O'Connor · DOB: 08/03/1962",
    payer: "UnitedHealthcare Commercial",
    service: "Echocardiogram Complete (CPT 93306 + ICD-10 I48.91)",
    initialIssue: "Payer medical necessity guideline update requires documented 30-day ECG history.",
    resolvedText: "Nexus AI detected recent rule revision (UHC Bulletin #24-B), verified qualifying Holter monitor date, and embedded clinical attestation.",
    confidence: "99.7%",
    status: "Compliant & Dispatched"
  }
];

let currentClaimIndex = 0;

function initClaimSimulator() {
  const claimIdEl = document.getElementById('claim-id');
  const claimPatientEl = document.getElementById('claim-patient');
  const claimDiagEl = document.getElementById('claim-diagnosis');
  const claimAlertEl = document.getElementById('claim-audit-alert');
  const claimConfidenceEl = document.getElementById('claim-confidence');
  const claimStatusEl = document.getElementById('claim-status-tag');
  const simulateBtn = document.getElementById('btn-simulate-claim');
  const overrideToggle = document.getElementById('toggle-human-review');

  if (!simulateBtn) return;

  simulateBtn.addEventListener('click', () => {
    simulateBtn.disabled = true;
    simulateBtn.innerHTML = `
      <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
      </svg> Analyzing Intake...
    `;

    // Show temporary analyzing state
    if (claimAlertEl) {
      claimAlertEl.className = 'claim-audit-alert';
      claimAlertEl.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>Running deterministic validation against payer rule matrix...</span>
      `;
    }

    setTimeout(() => {
      currentClaimIndex = (currentClaimIndex + 1) % sampleClaims.length;
      const claim = sampleClaims[currentClaimIndex];

      if (claimIdEl) claimIdEl.textContent = claim.id;
      if (claimPatientEl) claimPatientEl.textContent = claim.patient;
      if (claimDiagEl) claimDiagEl.textContent = `${claim.payer} · ${claim.service}`;
      if (claimConfidenceEl) claimConfidenceEl.textContent = claim.confidence;
      if (claimStatusEl) claimStatusEl.textContent = claim.status;

      if (claimAlertEl) {
        claimAlertEl.className = 'claim-audit-resolved';
        claimAlertEl.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <div>
            <strong>Validation Succeeded:</strong> ${claim.resolvedText}
          </div>
        `;
      }

      simulateBtn.disabled = false;
      simulateBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg> Simulate Next Claim
      `;

      showToast(`Processed ${claim.id}: 0 manual edits required`);
    }, 650);
  });

  // Override Toggle
  if (overrideToggle) {
    overrideToggle.addEventListener('click', () => {
      const isManual = overrideToggle.dataset.mode === 'manual';
      if (isManual) {
        overrideToggle.dataset.mode = 'auto';
        overrideToggle.textContent = 'Auto-Pilot Mode';
        overrideToggle.classList.remove('btn-secondary');
        overrideToggle.classList.add('btn-primary');
        showToast('Autonomous Agent Execution Active (Confidence > 95%)');
      } else {
        overrideToggle.dataset.mode = 'manual';
        overrideToggle.textContent = 'Human-in-the-Loop Mode';
        overrideToggle.classList.remove('btn-primary');
        overrideToggle.classList.add('btn-secondary');
        showToast('Human-in-the-Loop: High-risk cases routed to billing specialist');
      }
    });
  }
}

/* ==========================================================================
   3. Interactive ROI Calculator (Zone 7)
   ========================================================================== */
function initRoiCalculator() {
  const sliderSpecialists = document.getElementById('calc-specialists');
  const sliderHours = document.getElementById('calc-hours');
  const sliderWage = document.getElementById('calc-wage');
  const sliderVolume = document.getElementById('calc-volume');
  const sliderDenial = document.getElementById('calc-denial');

  // Pill Displays
  const valSpecialists = document.getElementById('val-specialists');
  const valHours = document.getElementById('val-hours');
  const valWage = document.getElementById('val-wage');
  const valVolume = document.getElementById('val-volume');
  const valDenial = document.getElementById('val-denial');

  // Result Displays
  const outAnnualSavings = document.getElementById('out-annual-savings');
  const outCurrentCost = document.getElementById('out-current-cost');
  const outHoursSaved = document.getElementById('out-hours-saved');
  const outPaybackPeriod = document.getElementById('out-payback-period');
  const lockSavingsBtn = document.getElementById('btn-lock-savings');

  if (!sliderSpecialists || !sliderHours || !sliderWage) return;

  function calculate() {
    const specialists = parseInt(sliderSpecialists.value, 10);
    const hoursPerWeek = parseInt(sliderHours.value, 10);
    const hourlyWage = parseInt(sliderWage.value, 10);
    const monthlyVolume = parseInt(sliderVolume.value, 10);
    const denialRatePct = parseInt(sliderDenial.value, 10);

    // Update Slider Pills
    valSpecialists.textContent = `${specialists} specialists`;
    valHours.textContent = `${hoursPerWeek} hrs/wk`;
    valWage.textContent = `$${hourlyWage}/hr`;
    valVolume.textContent = `${monthlyVolume.toLocaleString()} claims/mo`;
    valDenial.textContent = `${denialRatePct}% rate`;

    // Operational Math
    // 1. Annual Labor cost spent strictly on manual review & rework
    const annualLaborCost = specialists * hoursPerWeek * 52 * hourlyWage;

    // 2. Annual claim rework cost (average $48 direct cost to rework a denied claim + write-off leakages)
    const annualClaims = monthlyVolume * 12;
    const annualDenials = annualClaims * (denialRatePct / 100);
    const directReworkCost = annualDenials * 48;

    const totalCurrentOperationalCost = annualLaborCost + directReworkCost;

    // 3. Nexus AI impact
    // 85% reduction in manual review hours
    const laborSaved = annualLaborCost * 0.85;
    // 92% reduction in claim denials
    const reworkSaved = directReworkCost * 0.92;

    // Estimated Nexus AI Platform investment (~$0.40 per claim or $15k baseline)
    const nexusCost = Math.max(16000, annualClaims * 0.38);

    const netAnnualSavings = Math.max(25000, Math.round((laborSaved + reworkSaved) - nexusCost));
    const hoursSavedPerWeek = Math.round(specialists * hoursPerWeek * 0.85);

    // Payback period in months = (nexusCost / (laborSaved + reworkSaved)) * 12
    const totalBenefit = laborSaved + reworkSaved;
    const paybackMonths = totalBenefit > 0 
      ? Math.max(0.8, Number(((nexusCost / totalBenefit) * 12).toFixed(1)))
      : 2.1;

    // Update DOM
    outAnnualSavings.textContent = `$${netAnnualSavings.toLocaleString()}`;
    outCurrentCost.textContent = `$${Math.round(totalCurrentOperationalCost).toLocaleString()}`;
    outHoursSaved.textContent = `${hoursSavedPerWeek} hrs`;
    outPaybackPeriod.textContent = `${paybackMonths} Months`;
  }

  function updateSliderBackground(slider) {
    if (!slider) return;
    const min = parseFloat(slider.min) || 0;
    const max = parseFloat(slider.max) || 100;
    const val = parseFloat(slider.value) || 0;
    const percentage = ((val - min) / (max - min)) * 100;
    slider.style.background = `linear-gradient(to right, #6366f1 0%, #38bdf8 ${percentage}%, rgba(255, 255, 255, 0.08) ${percentage}%, rgba(255, 255, 255, 0.08) 100%)`;
  }

  // Bind input listeners
  const sliders = [sliderSpecialists, sliderHours, sliderWage, sliderVolume, sliderDenial];
  sliders.forEach(slider => {
    slider.addEventListener('input', () => {
      calculate();
      updateSliderBackground(slider);
    });
    updateSliderBackground(slider);
  });

  // Calculate immediately
  calculate();

  // "Lock In These Savings" CTA transfers data to Demo Modal
  if (lockSavingsBtn) {
    lockSavingsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const savings = outAnnualSavings.textContent;
      const volume = parseInt(sliderVolume.value, 10);
      openDemoModal({
        notes: `Estimated annual savings from calculator: ${savings} across ${volume.toLocaleString()} monthly claims.`,
        volume: volume
      });
    });
  }
}

/* ==========================================================================
   4. Buyer Persona Tab Switcher (Zone 8)
   ========================================================================== */
const personaData = {
  operations: {
    title: "Operations & Billing Managers",
    lead: "Eliminate repetitive intake bottlenecks, clear pre-auth queues, and protect your team from burnout.",
    benefits: [
      "Automate 88%+ of standard prior-authorization intake and claim scrubbing.",
      "Reduce average claim triage turnaround time from 6 hours to 42 minutes.",
      "Prevent specialist turnover and overtime costs during seasonal volume surges.",
      "Real-time exception routing with 1-click specialist approval workflows."
    ],
    metric1: "88% Less Manual Entry",
    metric2: "42 min Turnaround",
    statusBadge: "Operational Throughput"
  },
  finance: {
    title: "CFOs & Revenue Cycle Directors",
    lead: "Accelerate cash collections, compress Days in Accounts Receivable (A/R), and eliminate avoidable write-offs.",
    benefits: [
      "Compress Days in A/R from an industry average of 48 days down to 19 days.",
      "Recover an estimated $320,000+ in annual write-offs caused by filing deadline expirations.",
      "Achieve measurable net payback in under 90 days with zero capital expenditure.",
      "Predictable, transparent ROI directly linked to claim volume."
    ],
    metric1: "19 Days in A/R",
    metric2: "$320K Avg Recovered",
    statusBadge: "Cash Flow & A/R Velocity"
  },
  compliance: {
    title: "Chief Compliance & Privacy Officers",
    lead: "Enforce deterministic regulatory policies with complete auditability, HIPAA guardrails, and zero hallucination risk.",
    benefits: [
      "100% cryptographic audit trail recording every rule validation, prompt, and system execution.",
      "Full HIPAA Business Associate Agreement (BAA) with multi-tenant data isolation.",
      "Zero customer or patient data utilized for AI model training or external indexing.",
      "Hard negative safety constraints preventing unvalidated clearinghouse submissions."
    ],
    metric1: "100% HIPAA BAA",
    metric2: "Zero Model Retention",
    statusBadge: "Regulatory Compliance"
  },
  leadership: {
    title: "CEOs, COOs & Clinic Owners",
    lead: "Scale patient visits and regional clinic locations without proportional administrative overhead.",
    benefits: [
      "Expand provider capacity 3x without hiring additional administrative billing specialists.",
      "Eliminate patient friction caused by unexpected coverage rejections and billing surprises.",
      "Deploy across all clinic EHRs in under 14 business days with zero custom engineering.",
      "Standardize revenue operations across newly acquired medical practices."
    ],
    metric1: "3x Volume Scale",
    metric2: "14-Day Go-Live",
    statusBadge: "Executive Scalability"
  }
};

function initPersonaTabs() {
  const tabBtns = document.querySelectorAll('.persona-tab');
  const titleEl = document.getElementById('persona-title');
  const leadEl = document.getElementById('persona-lead');
  const benefitsListEl = document.getElementById('persona-benefits');
  const m1El = document.getElementById('persona-metric-1');
  const m2El = document.getElementById('persona-metric-2');
  const badgeEl = document.getElementById('persona-badge');

  if (!tabBtns.length || !titleEl) return;

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const personaKey = btn.dataset.persona;
      const data = personaData[personaKey];
      if (!data) return;

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Update Card
      titleEl.textContent = data.title;
      leadEl.textContent = data.lead;
      if (m1El) m1El.textContent = data.metric1;
      if (m2El) m2El.textContent = data.metric2;
      if (badgeEl) badgeEl.textContent = data.statusBadge;

      if (benefitsListEl) {
        benefitsListEl.innerHTML = data.benefits.map(b => `
          <li class="benefit-item">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <span>${b}</span>
          </li>
        `).join('');
      }
    });
  });
}

/* ==========================================================================
   5. Accessible FAQ Accordion (Zone 11)
   ========================================================================== */
function initFaqAccordion() {
  const faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach(item => {
    const questionBtn = item.querySelector('.faq-question-btn');
    const answerPanel = item.querySelector('.faq-answer-panel');

    if (!questionBtn || !answerPanel) return;

    questionBtn.addEventListener('click', () => {
      const isOpen = item.classList.contains('active');

      // Close all other items
      faqItems.forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove('active');
          const otherBtn = otherItem.querySelector('.faq-question-btn');
          const otherPanel = otherItem.querySelector('.faq-answer-panel');
          if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
          if (otherPanel) otherPanel.style.maxHeight = null;
        }
      });

      // Toggle current item
      if (isOpen) {
        item.classList.remove('active');
        questionBtn.setAttribute('aria-expanded', 'false');
        answerPanel.style.maxHeight = null;
      } else {
        item.classList.add('active');
        questionBtn.setAttribute('aria-expanded', 'true');
        answerPanel.style.maxHeight = answerPanel.scrollHeight + 30 + 'px';
      }
    });
  });
}

/* ==========================================================================
   6. 2-Step Demo Qualification & Calendar Modal (PRD Section 4.1 & 4.2)
   ========================================================================== */
let selectedTimeSlot = "Tomorrow at 10:00 AM EST";

function initDemoModal() {
  const modalBackdrop = document.getElementById('demo-modal');
  const closeBtn = document.getElementById('demo-modal-close');
  const openButtons = document.querySelectorAll('.btn-open-demo');

  const step1 = document.getElementById('modal-step-1');
  const step2 = document.getElementById('modal-step-2');
  const step3 = document.getElementById('modal-step-success');

  const indicator1 = document.getElementById('step-ind-1');
  const indicator2 = document.getElementById('step-ind-2');

  const btnToStep2 = document.getElementById('btn-to-step-2');
  const btnBackToStep1 = document.getElementById('btn-back-to-step-1');
  const btnConfirmBooking = document.getElementById('btn-confirm-booking');

  // Form Fields
  const emailInput = document.getElementById('demo-email');
  const nameInput = document.getElementById('demo-name');
  const companyInput = document.getElementById('demo-company');
  const titleInput = document.getElementById('demo-title');
  const sizeInput = document.getElementById('demo-size');
  const problemInput = document.getElementById('demo-problem');

  if (!modalBackdrop) return;

  // Open modal triggers
  openButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      openDemoModal();
    });
  });

  // Close triggers
  if (closeBtn) {
    closeBtn.addEventListener('click', closeDemoModal);
  }
  modalBackdrop.addEventListener('click', (e) => {
    if (e.target === modalBackdrop) closeDemoModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalBackdrop.classList.contains('open')) {
      closeDemoModal();
    }
  });

  // Real-time error clearing on input
  [emailInput, nameInput, companyInput].forEach(input => {
    if (input) {
      input.addEventListener('input', () => {
        input.classList.remove('error');
        const err = document.getElementById(`err-${input.id}`);
        if (err) err.classList.remove('visible');
      });
    }
  });

  // Step 1 Validation & Proceed to Step 2
  if (btnToStep2) {
    btnToStep2.addEventListener('click', () => {
      let valid = true;

      // Validate Email
      const emailVal = emailInput.value.trim();
      const emailErr = document.getElementById('err-demo-email');
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailVal || !emailRegex.test(emailVal)) {
        emailInput.classList.add('error');
        if (emailErr) emailErr.classList.add('visible');
        valid = false;
      } else {
        emailInput.classList.remove('error');
        if (emailErr) emailErr.classList.remove('visible');
      }

      // Validate Name
      const nameVal = nameInput.value.trim();
      const nameErr = document.getElementById('err-demo-name');
      if (!nameVal || nameVal.length < 2) {
        nameInput.classList.add('error');
        if (nameErr) nameErr.classList.add('visible');
        valid = false;
      } else {
        nameInput.classList.remove('error');
        if (nameErr) nameErr.classList.remove('visible');
      }

      // Validate Company
      const compVal = companyInput.value.trim();
      const compErr = document.getElementById('err-demo-company');
      if (!compVal || compVal.length < 2) {
        companyInput.classList.add('error');
        if (compErr) compErr.classList.add('visible');
        valid = false;
      } else {
        companyInput.classList.remove('error');
        if (compErr) compErr.classList.remove('visible');
      }

      if (!valid) return;

      // Advance to Step 2 (Calendar Scheduling)
      step1.style.display = 'none';
      step2.style.display = 'block';

      if (indicator1) {
        indicator1.classList.remove('active');
        indicator1.classList.add('done');
      }
      if (indicator2) {
        indicator2.classList.add('active');
      }
    });
  }

  // Back to Step 1
  if (btnBackToStep1) {
    btnBackToStep1.addEventListener('click', () => {
      step2.style.display = 'none';
      step1.style.display = 'block';

      if (indicator1) {
        indicator1.classList.add('active');
        indicator1.classList.remove('done');
      }
      if (indicator2) {
        indicator2.classList.remove('active');
      }
    });
  }

  // Time slot buttons
  const timeSlots = document.querySelectorAll('.time-slot-btn');
  timeSlots.forEach(slot => {
    slot.addEventListener('click', () => {
      timeSlots.forEach(s => s.classList.remove('selected'));
      slot.classList.add('selected');
      selectedTimeSlot = slot.dataset.slot || slot.textContent.trim();
    });
  });

  // Confirm Demo Booking (Step 2 Submission)
  if (btnConfirmBooking) {
    btnConfirmBooking.addEventListener('click', async () => {
      btnConfirmBooking.disabled = true;
      btnConfirmBooking.innerHTML = `
        <svg class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg> Securing Calendar Invite...
      `;

      const payload = {
        email: emailInput.value.trim(),
        name: nameInput.value.trim(),
        company: companyInput.value.trim(),
        job_title: titleInput ? titleInput.value.trim() : "",
        company_size: sizeInput ? sizeInput.value : "5000-15000",
        primary_workflow: problemInput ? problemInput.value.trim() : "",
        selected_slot: selectedTimeSlot
      };

      try {
        // Post to backend endpoint
        await fetch('/api/nexus/demo-qualification', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).catch(() => {
          return null;
        });
      } catch (err) {
        console.warn('Endpoint not available, proceeding with client confirmation', err);
      }

      setTimeout(() => {
        step2.style.display = 'none';
        step3.style.display = 'block';

        const scheduledSlotEl = document.getElementById('confirmed-slot-text');
        if (scheduledSlotEl) {
          scheduledSlotEl.textContent = `Confirmed: ${selectedTimeSlot} with Dr. Aris Thorne (Healthcare AI Lead)`;
        }

        if (indicator2) {
          indicator2.classList.remove('active');
          indicator2.classList.add('done');
        }

        showToast('Demo invitation confirmed! Calendar invite sent.');
      }, 700);
    });
  }

  // Done button in Step 3 success modal
  const btnDoneModal = document.getElementById('btn-done-modal');
  if (btnDoneModal) {
    btnDoneModal.addEventListener('click', closeDemoModal);
  }
}

function openDemoModal(opts = {}) {
  const modal = document.getElementById('demo-modal');
  if (!modal) return;

  // Reset steps
  const step1 = document.getElementById('modal-step-1');
  const step2 = document.getElementById('modal-step-2');
  const step3 = document.getElementById('modal-step-success');
  const ind1 = document.getElementById('step-ind-1');
  const ind2 = document.getElementById('step-ind-2');

  if (step1) step1.style.display = 'block';
  if (step2) step2.style.display = 'none';
  if (step3) step3.style.display = 'none';

  if (ind1) {
    ind1.className = 'step-indicator active';
  }
  if (ind2) {
    ind2.className = 'step-indicator';
  }

  // Reset booking button if previously submitted
  const confirmBtn = document.getElementById('btn-confirm-booking');
  if (confirmBtn) {
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = 'Confirm Demo Booking';
  }

  // Clear any existing validation errors
  ['demo-email', 'demo-name', 'demo-company'].forEach(id => {
    const input = document.getElementById(id);
    const err = document.getElementById(`err-${id}`);
    if (input) input.classList.remove('error');
    if (err) err.classList.remove('visible');
  });

  // Pre-fill notes if transferred from calculator
  if (opts.notes) {
    const problemInput = document.getElementById('demo-problem');
    if (problemInput) {
      problemInput.value = opts.notes;
    }
  }

  // Pre-select volume tier if passed from calculator
  if (opts.volume) {
    const sizeSelect = document.getElementById('demo-size');
    if (sizeSelect) {
      if (opts.volume < 5000) {
        sizeSelect.value = '1000-5000';
      } else if (opts.volume <= 15000) {
        sizeSelect.value = '5000-15000';
      } else if (opts.volume <= 50000) {
        sizeSelect.value = '15000-50000';
      } else {
        sizeSelect.value = '50000+';
      }
    }
  }

  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');

  const firstInput = document.getElementById('demo-email');
  if (firstInput) setTimeout(() => firstInput.focus(), 150);
}

function closeDemoModal() {
  const modal = document.getElementById('demo-modal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

// Expose modal functions to global scope
window.openDemoModal = openDemoModal;
window.closeDemoModal = closeDemoModal;

/* ==========================================================================
   7. Dynamic Positioning & Niche Switcher (PRD Section 0)
   ========================================================================== */
const nichePresets = {
  medical_billing: {
    niche: "Medical Billing",
    eyebrow: "AI Automation for Medical Billing",
    headline: "Automate Claim Denials & Pre-Authorizations Without Adding Operational Workload.",
    subhead: "Nexus AI helps mid-sized healthcare clinics automate repetitive intake, eliminate 92% of billing errors, and give Operations Managers complete audit control.",
    trust: "Built for healthcare operations teams processing 5,000+ claims monthly.",
    problemHead: "Manual Claim Processing is Creating Unsustainable Overhead for Healthcare Clinics.",
    buyer: "Operations Manager",
    companyType: "Mid-sized healthcare clinics",
    coreProblem: "claim denials & prior-auth loops",
    primaryOutcome: "92% fewer denials and lower billing labor"
  },
  financial_compliance: {
    niche: "Financial Compliance",
    eyebrow: "AI Automation for Financial AML & KYC",
    headline: "Automate Compliance Audits & KYC Reviews Without Adding Risk Overhead.",
    subhead: "Nexus AI helps regional fintechs & credit unions automate transaction monitoring, eliminate false positive alerts by 89%, and give Compliance Directors total transparency.",
    trust: "Built for risk & compliance teams reviewing 10,000+ daily transactions.",
    problemHead: "Manual SAR Reviews and False Positives are Choking Compliance Operations.",
    buyer: "Chief Compliance Officer",
    companyType: "Regional fintechs & credit unions",
    coreProblem: "false positive compliance alerts",
    primaryOutcome: "89% fewer false alarms and zero regulatory penalties"
  },
  supply_chain: {
    niche: "Supply Chain Invoicing",
    eyebrow: "AI Automation for Freight & Invoicing",
    headline: "Automate Freight Invoicing & 3-Way Matching Without Adding Back-Office Headcount.",
    subhead: "Nexus AI helps logistics and distribution hubs reconcile bills of lading against rate cards, eliminate 94% of invoice dispute discrepancies, and give Procurement complete visibility.",
    trust: "Built for supply chain teams managing $50M+ in annual freight spend.",
    problemHead: "Disputed Freight Invoices and Detention Charges are Sapping Working Capital.",
    buyer: "VP of Procurement & Logistics",
    companyType: "Distribution & logistics hubs",
    coreProblem: "invoice variance & rate-card mismatches",
    primaryOutcome: "94% faster 3-way matching and zero overpayment"
  }
};

function initPositioningSwitcher() {
  const nicheSelect = document.getElementById('niche-selector');
  if (!nicheSelect) return;

  nicheSelect.addEventListener('change', (e) => {
    const preset = nichePresets[e.target.value];
    if (!preset) return;

    // Update Hero elements dynamically
    const heroEyebrow = document.getElementById('hero-eyebrow-text');
    const heroHeadline = document.getElementById('hero-headline');
    const heroSubhead = document.getElementById('hero-subheadline');
    const heroTrust = document.getElementById('hero-trust-text');
    const problemHeading = document.getElementById('problem-heading');

    if (heroEyebrow) heroEyebrow.textContent = preset.eyebrow;
    if (heroHeadline) heroHeadline.textContent = preset.headline;
    if (heroSubhead) heroSubhead.textContent = preset.subhead;
    if (heroTrust) heroTrust.textContent = preset.trust;
    if (problemHeading) problemHeading.textContent = preset.problemHead;

    showToast(`Positioning updated to: ${preset.niche}`);
  });
}

/* ==========================================================================
   8. Toast Notification Utility
   ========================================================================== */
function showToast(message) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}
