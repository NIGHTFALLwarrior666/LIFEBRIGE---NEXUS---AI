/**
 * LifeBridge AI — Client-Side Application Controller
 * High-Stakes Societal Benefit AI Hackathon Entry
 * Accessible, Responsive, WCAG 2.1 AA Compliant
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const form = document.getElementById('emergency-form');
  const textArea = document.getElementById('incident-text');
  const charCounter = document.getElementById('char-counter');
  const fileInput = document.getElementById('incident-file');
  const fileDropzone = document.getElementById('file-dropzone');
  const filePreview = document.getElementById('file-attachment-preview');
  const attachmentName = document.getElementById('attachment-name');
  const attachmentSize = document.getElementById('attachment-size');
  const attachmentIcon = document.getElementById('attachment-type-icon');
  const removeAttachmentBtn = document.getElementById('remove-attachment-btn');

  const micBtn = document.getElementById('mic-record-btn');
  const micLabel = document.getElementById('mic-btn-label');
  const recIndicator = document.getElementById('recording-live-indicator');
  const recTimer = document.getElementById('recording-timer');

  const analyzeBtn = document.getElementById('analyze-btn');
  const analyzeBtnText = document.getElementById('analyze-btn-text');
  const analyzeSpinner = document.getElementById('analyze-spinner');
  const clearInputBtn = document.getElementById('clear-input-btn');

  const processingCard = document.getElementById('processing-pipeline-status');
  const processingStepTitle = document.getElementById('processing-step-title');
  const processingStepSubtitle = document.getElementById('processing-step-subtitle');
  const progressBarFill = document.getElementById('progress-bar-fill');

  const errorAlert = document.getElementById('error-alert');
  const errorTitle = document.getElementById('error-title');
  const errorMessage = document.getElementById('error-message');
  const errorCloseBtn = document.getElementById('error-close-btn');

  const resultsDashboard = document.getElementById('results-dashboard');
  const copySummaryBtn = document.getElementById('copy-summary-btn');
  const copyBtnLabel = document.getElementById('copy-btn-label');
  const newAnalysisBtn = document.getElementById('new-analysis-btn');

  // Status and Engine Badges
  const systemStatusIndicator = document.getElementById('system-status-indicator');
  const systemStatusText = document.getElementById('system-status-text');
  const globalModeLabel = document.getElementById('global-mode-label');

  // Media Recording State
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingInterval = null;
  let recordingSeconds = 0;
  let recordedAudioFile = null;

  // Selected File State
  let activeFile = null;
  let currentAnalysisData = null;

  // 1. Initial System Health Check
  async function checkHealth() {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        systemStatusText.textContent = 'System Operational';
        if (data.gemini_configured) {
          globalModeLabel.textContent = 'Gemini 2.5 Active';
        } else {
          globalModeLabel.textContent = 'Demo / Safe Fallback Active';
        }
      }
    } catch (err) {
      systemStatusText.textContent = 'Offline Fallback Ready';
      globalModeLabel.textContent = 'Deterministic Safe Mode';
    }
  }
  checkHealth();

  // 2. Character Counter
  textArea.addEventListener('input', () => {
    const len = textArea.value.length;
    charCounter.textContent = `${len.toLocaleString()} / 10,000`;
  });

  // 3. File Dropzone & Drag-and-Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    fileDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      fileDropzone.style.borderColor = 'var(--accent-google-blue)';
      fileDropzone.style.background = 'rgba(56, 189, 248, 0.08)';
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    fileDropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      fileDropzone.style.borderColor = '';
      fileDropzone.style.background = '';
    });
  });

  fileDropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function handleFileSelected(file) {
    // Validate size (< 10MB)
    if (file.size > 10 * 1024 * 1024) {
      showError('File Too Large', 'Maximum supported attachment size is 10MB.');
      return;
    }

    activeFile = file;
    recordedAudioFile = null; // override mic if file chosen

    // Format size
    const sizeFormatted = file.size > 1024 * 1024 
      ? (file.size / (1024 * 1024)).toFixed(1) + ' MB' 
      : Math.round(file.size / 1024) + ' KB';

    attachmentName.textContent = file.name;
    attachmentSize.textContent = `(${sizeFormatted})`;

    if (file.type.startsWith('image/')) {
      attachmentIcon.textContent = '🖼️';
    } else if (file.type.startsWith('audio/')) {
      attachmentIcon.textContent = '🎙️';
    } else {
      attachmentIcon.textContent = '📎';
    }

    filePreview.classList.remove('hidden');
    clearError();
  }

  removeAttachmentBtn.addEventListener('click', () => {
    activeFile = null;
    recordedAudioFile = null;
    fileInput.value = '';
    filePreview.classList.add('hidden');
  });

  // 4. Voice Recording Module (Web Audio MediaRecorder)
  micBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      stopRecording();
    } else {
      startRecording();
    }
  });

  async function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError('Microphone Unavailable', 'Audio recording is not supported in this browser environment. You can upload an audio file instead.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        recordedAudioFile = new File([audioBlob], `voice_dispatch_${Date.now()}.webm`, { type: 'audio/webm' });
        handleFileSelected(recordedAudioFile);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      micBtn.classList.add('recording');
      micLabel.textContent = 'Stop Recording';
      recIndicator.classList.remove('hidden');

      recordingSeconds = 0;
      recTimer.textContent = '00:00';
      recordingInterval = setInterval(() => {
        recordingSeconds++;
        const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, '0');
        const secs = String(recordingSeconds % 60).padStart(2, '0');
        recTimer.textContent = `${mins}:${secs}`;
      }, 1000);

      clearError();
    } catch (err) {
      showError('Microphone Permission Denied', 'Please grant microphone access or use file upload.');
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      clearInterval(recordingInterval);
      micBtn.classList.remove('recording');
      micLabel.textContent = 'Record Voice Note';
      recIndicator.classList.add('hidden');
    }
  }

  // 5. 1-Click Demo Scenarios
  document.querySelectorAll('.demo-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const scenario = btn.getAttribute('data-scenario');
      
      // Visual feedback
      if (scenario === 'road_accident') {
        textArea.value = 'Highway collision at mile marker 42 on Route 9 southbound. Two vehicles involved; sedan crushed with trapped driver, engine bay smoking with gasoline leak. Overturned car in ditch.';
      } else if (scenario === 'flood_rescue') {
        textArea.value = 'Flash flood water rising to 6 feet in residential cul-de-sac. Family of 4 stranded on pitched roof with toddler. Rapid brown current with submerged electrical transformer buzzing nearby.';
      } else if (scenario === 'medical_note') {
        textArea.value = 'Handwritten medication note for 78yo cardiac patient: ambiguous dosage reading 10mg or .10mg of blood thinner, alongside penicillin-class antibiotic order despite documented severe allergy.';
      }
      charCounter.textContent = `${textArea.value.length} / 10,000`;

      // Trigger deterministic execution
      submitAnalysis(null, scenario);
    });
  });

  // 6. Form Submission
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = textArea.value.trim();
    const file = activeFile || recordedAudioFile;

    if (!text && !file) {
      showError('Input Required', 'Please provide a situational description, attach an image/audio file, or select a demo scenario.');
      textArea.focus();
      return;
    }

    submitAnalysis({ text, file }, null);
  });

  // Reset Console
  clearInputBtn.addEventListener('click', resetConsole);
  newAnalysisBtn.addEventListener('click', () => {
    resetConsole();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  function resetConsole() {
    textArea.value = '';
    charCounter.textContent = '0 / 10,000';
    activeFile = null;
    recordedAudioFile = null;
    fileInput.value = '';
    filePreview.classList.add('hidden');
    resultsDashboard.classList.add('hidden');
    clearError();
  }

  // 7. Core Analysis Pipeline
  async function submitAnalysis(inputData, demoScenario) {
    clearError();
    setLoadingState(true);

    const formData = new FormData();
    if (demoScenario) {
      formData.append('demo_scenario', demoScenario);
    } else {
      if (inputData.text) formData.append('text', inputData.text);
      if (inputData.file) formData.append('file', inputData.file);
    }

    // Pipeline progress animation steps
    simulatePipelineProgress();

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.message || `Server error (${response.status})`);
      }

      const data = await response.json();
      currentAnalysisData = data;

      // Complete progress bar
      progressBarFill.style.width = '100%';
      setTimeout(() => {
        setLoadingState(false);
        renderResults(data);
        resultsDashboard.classList.remove('hidden');
        resultsDashboard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 400);

    } catch (err) {
      setLoadingState(false);
      showError('Analysis Failed', err.message || 'Unable to process incident at this time. Safe emergency fallback protocol recommended.');
    }
  }

  function simulatePipelineProgress() {
    progressBarFill.style.width = '15%';
    processingStepTitle.textContent = 'Ingesting Multimodal Incident Data...';
    processingStepSubtitle.textContent = 'Validating input parameters and MIME allowlists';

    setTimeout(() => {
      progressBarFill.style.width = '45%';
      processingStepTitle.textContent = 'Gemini Multimodal Understanding...';
      processingStepSubtitle.textContent = 'Extracting factual incident context and hazards';
    }, 400);

    setTimeout(() => {
      progressBarFill.style.width = '75%';
      processingStepTitle.textContent = 'Deterministic Safety Rules & Clamping...';
      processingStepSubtitle.textContent = 'Enforcing critical escalation and negative constraints';
    }, 800);
  }

  function setLoadingState(isLoading) {
    if (isLoading) {
      analyzeBtn.disabled = true;
      analyzeSpinner.classList.remove('hidden');
      analyzeBtnText.classList.add('hidden');
      processingCard.classList.remove('hidden');
    } else {
      analyzeBtn.disabled = false;
      analyzeSpinner.classList.add('hidden');
      analyzeBtnText.classList.remove('hidden');
      processingCard.classList.add('hidden');
    }
  }

  // 8. Results Rendering Engine
  function renderResults(data) {
    // 1. Engine / Mode Badge
    const engineBadge = document.getElementById('result-engine-badge');
    if (data.mode === 'gemini') {
      engineBadge.className = 'engine-badge gemini';
      engineBadge.textContent = '✦ Gemini AI Verified';
    } else {
      engineBadge.className = 'engine-badge fallback';
      engineBadge.textContent = '⚠️ Demo / Fallback Guidance';
    }

    // 2. Incident Title & Timestamp
    document.getElementById('dashboard-heading').textContent = data.incident_type || 'Emergency Incident';
    document.getElementById('result-timestamp').textContent = new Date(data.timestamp).toLocaleString() + ' UTC';

    // 3. Severity Indicator
    const sevVal = document.getElementById('result-severity-val');
    const sevDot = document.getElementById('severity-dot');
    const sevBox = document.getElementById('severity-metric-box');

    sevVal.textContent = data.severity;
    sevBox.className = 'metric-card severity-card';
    sevDot.className = 'severity-indicator-dot';

    const sevKey = data.severity.toLowerCase();
    if (sevKey === 'critical') {
      sevVal.className = 'metric-val sev-critical-val';
      sevDot.classList.add('sev-critical-dot');
      sevBox.classList.add('sev-critical-box');
    } else if (sevKey === 'high') {
      sevVal.className = 'metric-val sev-high-val';
      sevDot.classList.add('sev-high-dot');
      sevBox.classList.add('sev-high-box');
    } else if (sevKey === 'moderate') {
      sevVal.className = 'metric-val sev-moderate-val';
      sevDot.classList.add('sev-moderate-dot');
      sevBox.classList.add('sev-moderate-box');
    } else {
      sevVal.className = 'metric-val sev-low-val';
      sevDot.classList.add('sev-low-dot');
      sevBox.classList.add('sev-low-box');
    }

    // 4. Escalation Protocol
    const escVal = document.getElementById('result-escalation-val');
    const escIcon = document.getElementById('escalation-icon');
    const escBox = document.getElementById('escalation-metric-box');

    escVal.textContent = data.escalation_required.replace(/_/g, ' ');
    if (data.escalation_required === 'EMERGENCY_SERVICES') {
      escIcon.textContent = '🚨';
      escVal.style.color = 'var(--sev-critical)';
    } else if (data.escalation_required === 'CONTACT_AUTHORITY') {
      escIcon.textContent = '⚠️';
      escVal.style.color = 'var(--sev-high)';
    } else {
      escIcon.textContent = '👁️';
      escVal.style.color = 'var(--sev-moderate)';
    }

    // 5. Confidence Clamped Score
    const confPct = Math.round(data.confidence * 100);
    document.getElementById('result-confidence-val').textContent = `${confPct}%`;
    const confStatus = document.getElementById('result-confidence-status');
    if (confPct >= 80) {
      confStatus.textContent = '(High Precision)';
      confStatus.style.color = '#34d399';
    } else if (confPct >= 60) {
      confStatus.textContent = '(Moderate Certainty)';
      confStatus.style.color = '#fbbf24';
    } else {
      confStatus.textContent = '(Elevated Uncertainty)';
      confStatus.style.color = '#f43f5e';
    }

    // 6. Situational Understanding & Evidence
    document.getElementById('result-summary-text').textContent = data.summary;
    renderList('result-evidence-list', data.sources_or_evidence, 'No direct evidence tags recorded.');

    // 7. Immediate Actions
    renderList('result-actions-list', data.recommended_actions, 'Maintain safety perimeter and wait for assistance.');

    // 8. DO NOT DO Constraints
    renderList('result-dnd-list', data.do_not_do, 'Do not approach active hazards without protective gear.');

    // 9. Hazards Chips
    const hazardsContainer = document.getElementById('result-hazards-list');
    hazardsContainer.innerHTML = '';
    if (data.detected_hazards && data.detected_hazards.length > 0) {
      data.detected_hazards.forEach(hazard => {
        const chip = document.createElement('div');
        chip.className = 'hazard-chip';
        chip.textContent = hazard;
        hazardsContainer.appendChild(chip);
      });
    } else {
      hazardsContainer.innerHTML = '<div class="hazard-chip">No specific hazards confirmed.</div>';
    }

    // 10. Missing Information & Uncertainties
    renderList('result-missing-list', data.missing_information, 'Baseline situational requirements satisfied.');
    renderList('result-uncertainties-list', data.uncertainties, 'No unresolved assertions noted.');

    // 11. Deterministic Validation Audit Log
    const auditContainer = document.getElementById('validation-records-container');
    if (data.validation_records && data.validation_records.length > 0) {
      let tableHtml = `
        <table class="validation-table">
          <thead>
            <tr>
              <th>Rule ID</th>
              <th>Deterministic Action</th>
              <th>Original</th>
              <th>Verified Safe</th>
            </tr>
          </thead>
          <tbody>
      `;
      data.validation_records.forEach(rec => {
        tableHtml += `
          <tr>
            <td><span class="rule-id-badge">${rec.rule_id}</span></td>
            <td>${rec.description}</td>
            <td><code>${rec.original_value || 'None'}</code></td>
            <td><strong><code>${rec.corrected_value || 'Applied'}</code></strong></td>
          </tr>
        `;
      });
      tableHtml += '</tbody></table>';
      auditContainer.innerHTML = tableHtml;
    } else {
      auditContainer.innerHTML = `
        <div class="audit-clean-state">
          <span>✓</span> All outputs passed deterministic schema validation cleanly without requiring safety overrides.
        </div>
      `;
    }

    // 12. Disclaimer
    document.getElementById('result-disclaimer-text').textContent = data.disclaimer;
  }

  function renderList(elementId, items, emptyText) {
    const el = document.getElementById(elementId);
    el.innerHTML = '';
    if (items && items.length > 0) {
      items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        el.appendChild(li);
      });
    } else {
      const li = document.createElement('li');
      li.textContent = emptyText;
      el.appendChild(li);
    }
  }

  // 9. Copy Briefing to Clipboard
  copySummaryBtn.addEventListener('click', async () => {
    if (!currentAnalysisData) return;

    const data = currentAnalysisData;
    const briefing = `
[ LIFEBRIDGE AI EMERGENCY BRIEFING ]
------------------------------------
INCIDENT: ${data.incident_type}
SEVERITY: ${data.severity}
ESCALATION: ${data.escalation_required}
CONFIDENCE: ${Math.round(data.confidence * 100)}%
MODE: ${data.mode.toUpperCase()}
TIMESTAMP: ${data.timestamp}

SITUATION SUMMARY:
${data.summary}

PRIORITIZED ACTIONS:
${data.recommended_actions.map((act, i) => `${i + 1}. ${act}`).join('\n')}

DO NOT DO (CRITICAL CONSTRAINTS):
${data.do_not_do.map(dnd => `⛔ ${dnd}`).join('\n')}

DETECTED HAZARDS:
${data.detected_hazards.map(h => `⚠️ ${h}`).join('\n')}

MISSING INFORMATION TO VERIFY:
${data.missing_information.map(m => `? ${m}`).join('\n')}

DISCLAIMER:
${data.disclaimer}
    `.trim();

    try {
      await navigator.clipboard.writeText(briefing);
      copyBtnLabel.textContent = 'Copied!';
      setTimeout(() => {
        copyBtnLabel.textContent = 'Copy Briefing';
      }, 2000);
    } catch (err) {
      showError('Clipboard Error', 'Please select and copy manually.');
    }
  });

  // 10. Error Handling Utilities
  function showError(title, msg) {
    errorTitle.textContent = title;
    errorMessage.textContent = msg;
    errorAlert.classList.remove('hidden');
    errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function clearError() {
    errorAlert.classList.add('hidden');
  }

  errorCloseBtn.addEventListener('click', clearError);
});
