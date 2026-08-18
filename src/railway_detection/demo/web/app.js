/**
 * AI Railway Crossing Safety — Interactive Dashboard Client Application
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let activeVideoPath = null;
  let activeJobId = null;
  let pollInterval = null;
  let lastCompletedSummary = null;

  // DOM Elements
  const navTabs = document.querySelectorAll(".nav-tab");
  const tabPanes = document.querySelectorAll(".tab-pane");

  // Video Tab Elements
  const videoDropzone = document.getElementById("videoDropzone");
  const videoFileInput = document.getElementById("videoFileInput");
  const fileSelectedIndicator = document.getElementById("fileSelectedIndicator");
  const selectedFileName = document.getElementById("selectedFileName");
  const btnClearFile = document.getElementById("btnClearFile");

  const confRange = document.getElementById("confRange");
  const confVal = document.getElementById("confVal");
  const iouRange = document.getElementById("iouRange");
  const iouVal = document.getElementById("iouVal");
  const deviceSelect = document.getElementById("deviceSelect");
  const temporalToggle = document.getElementById("temporalToggle");
  const btnStartProcessing = document.getElementById("btnStartProcessing");

  const progressContainer = document.getElementById("progressContainer");
  const progressStatusText = document.getElementById("progressStatusText");
  const progressPct = document.getElementById("progressPct");
  const progressBarFill = document.getElementById("progressBarFill");
  const frameCounterText = document.getElementById("frameCounterText");
  const liveCountFront = document.getElementById("liveCountFront");
  const liveCountSide = document.getElementById("liveCountSide");
  const liveCountRear = document.getElementById("liveCountRear");

  const emptyVideoState = document.getElementById("emptyVideoState");
  const videoPlayerContainer = document.getElementById("videoPlayerContainer");
  const processedVideoPlayer = document.getElementById("processedVideoPlayer");
  const videoSource = document.getElementById("videoSource");

  const analyticsSection = document.getElementById("analyticsSection");
  const resFrames = document.getElementById("resFrames");
  const resDuration = document.getElementById("resDuration");
  const resFps = document.getElementById("resFps");
  const resDevice = document.getElementById("resDevice");
  const resTotalDets = document.getElementById("resTotalDets");
  const resOccupancy = document.getElementById("resOccupancy");
  const classSummaryTableBody = document.getElementById("classSummaryTableBody");
  const btnDownloadVideo = document.getElementById("btnDownloadVideo");
  const btnViewSummaryMd = document.getElementById("btnViewSummaryMd");

  // Single-Image Tab Elements
  const imageDropzone = document.getElementById("imageDropzone");
  const imageFileInput = document.getElementById("imageFileInput");
  const imgConfRange = document.getElementById("imgConfRange");
  const imgConfVal = document.getElementById("imgConfVal");
  const btnTestImage = document.getElementById("btnTestImage");
  const emptyImageState = document.getElementById("emptyImageState");
  const imageResultContainer = document.getElementById("imageResultContainer");
  const annotatedImagePreview = document.getElementById("annotatedImagePreview");
  const imageStatsFooter = document.getElementById("imageStatsFooter");

  // History Tab Elements
  const historyListContainer = document.getElementById("historyListContainer");
  const btnRefreshHistory = document.getElementById("btnRefreshHistory");

  // Modal Elements
  const mdModal = document.getElementById("mdModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const mdModalContent = document.getElementById("mdModalContent");

  // --- TAB NAVIGATION ---
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      navTabs.forEach((t) => t.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const targetPane = document.getElementById(tab.dataset.tab);
      if (targetPane) {
        targetPane.classList.add("active");
      }

      if (tab.dataset.tab === "tabHistory") {
        loadHistoryRuns();
      } else if (tab.dataset.tab === "tabBenchmark") {
        loadBenchmarkData();
      }
    });
  });

  // --- INITIALIZE SYSTEM STATUS ---
  fetch("/api/status")
    .then((r) => r.json())
    .then((status) => {
      const devText = document.getElementById("deviceText");
      if (status.device_capabilities?.mps_available) {
        devText.textContent = "Apple Silicon MPS Active";
      } else if (status.device_capabilities?.cuda_available) {
        devText.textContent = "CUDA GPU Active";
      } else {
        devText.textContent = "CPU Device Active";
      }
    })
    .catch(() => {});

  // --- SLIDER VALUE BINDINGS ---
  confRange.addEventListener("input", (e) => {
    confVal.textContent = parseFloat(e.target.value).toFixed(2);
  });
  iouRange.addEventListener("input", (e) => {
    iouVal.textContent = parseFloat(e.target.value).toFixed(2);
  });
  imgConfRange.addEventListener("input", (e) => {
    imgConfVal.textContent = parseFloat(e.target.value).toFixed(2);
  });

  // --- VIDEO UPLOAD & SELECTION ---
  videoDropzone.addEventListener("click", () => videoFileInput.click());
  videoDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    videoDropzone.classList.add("dragover");
  });
  videoDropzone.addEventListener("dragleave", () => {
    videoDropzone.classList.remove("dragover");
  });
  videoDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    videoDropzone.classList.remove("dragover");
    if (e.dataTransfer.files?.length > 0) {
      handleVideoFile(e.dataTransfer.files[0]);
    }
  });
  videoFileInput.addEventListener("change", (e) => {
    if (e.target.files?.length > 0) {
      handleVideoFile(e.target.files[0]);
    }
  });

  btnClearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    activeVideoPath = null;
    videoFileInput.value = "";
    fileSelectedIndicator.style.display = "none";
    videoDropzone.querySelector(".dropzone-content").style.display = "block";
    btnStartProcessing.disabled = true;
  });

  function handleVideoFile(file) {
    selectedFileName.textContent = file.name;
    fileSelectedIndicator.style.display = "flex";
    videoDropzone.querySelector(".dropzone-content").style.display = "none";

    const formData = new FormData();
    formData.append("video", file);

    progressStatusText.textContent = "Uploading video...";
    btnStartProcessing.disabled = true;

    fetch("/api/upload", {
      method: "POST",
      body: formData,
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.full_path) {
          activeVideoPath = data.full_path;
          btnStartProcessing.disabled = false;
        } else {
          alert("Upload failed: " + (data.error || "Unknown error"));
        }
      })
      .catch((err) => {
        alert("Upload error: " + err);
      });
  }

  // --- START VIDEO PROCESSING ---
  btnStartProcessing.addEventListener("click", () => {
    if (!activeVideoPath) return;

    btnStartProcessing.disabled = true;
    progressContainer.style.display = "block";
    progressBarFill.style.width = "0%";
    progressPct.textContent = "0%";
    progressStatusText.textContent = "Initializing YOLO model...";

    emptyVideoState.style.display = "none";
    videoPlayerContainer.style.display = "none";
    analyticsSection.style.display = "none";

    const payload = {
      video_path: activeVideoPath,
      conf: parseFloat(confRange.value),
      iou: parseFloat(iouRange.value),
      device: deviceSelect.value,
      temporal: temporalToggle.checked,
    };

    fetch("/api/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.job_id) {
          activeJobId = data.job_id;
          startPollingProgress(activeJobId);
        } else {
          alert("Failed to start processing: " + (data.error || "Unknown error"));
          btnStartProcessing.disabled = false;
        }
      })
      .catch((err) => {
        alert("Error starting job: " + err);
        btnStartProcessing.disabled = false;
      });
  });

  function startPollingProgress(jobId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(() => {
      fetch(`/api/progress/${jobId}`)
        .then((r) => r.json())
        .then((job) => {
          if (!job || job.error) return;

          progressBarFill.style.width = `${job.progress_pct}%`;
          progressPct.textContent = `${job.progress_pct.toFixed(0)}%`;
          frameCounterText.textContent = `Frame ${job.current_frame} / ${job.total_frames || "?"}`;

          if (job.active_counts) {
            liveCountFront.textContent = job.active_counts.front || 0;
            liveCountSide.textContent = job.active_counts.side || 0;
            liveCountRear.textContent = job.active_counts.rear || 0;
          }

          if (job.status === "completed") {
            clearInterval(pollInterval);
            onProcessingCompleted(job);
          } else if (job.status === "failed") {
            clearInterval(pollInterval);
            progressStatusText.textContent = "Processing Failed: " + (job.error || "Unknown error");
            btnStartProcessing.disabled = false;
          }
        })
        .catch(() => {});
    }, 400);
  }

  function onProcessingCompleted(job) {
    progressStatusText.textContent = "Processing Completed!";
    progressBarFill.style.width = "100%";
    progressPct.textContent = "100%";
    btnStartProcessing.disabled = false;

    lastCompletedSummary = job.summary;

    // Load video
    if (job.video_url) {
      videoSource.src = job.video_url;
      processedVideoPlayer.load();
      videoPlayerContainer.style.display = "block";
      btnDownloadVideo.href = job.video_url;
    }

    // Render summary analytics
    if (job.summary) {
      renderSummaryAnalytics(job.summary);
    }
  }

  function renderSummaryAnalytics(sum) {
    analyticsSection.style.display = "block";

    resFrames.textContent = sum.video_metadata?.processed_frames || 0;
    resDuration.textContent = `${(sum.performance?.duration_seconds || 0).toFixed(2)}s total`;
    resFps.textContent = `${(sum.performance?.average_inference_fps || 0).toFixed(1)} FPS`;
    resDevice.textContent = (sum.device_used || "mps").toUpperCase();
    resTotalDets.textContent = sum.detection_overview?.total_detections || 0;
    resOccupancy.textContent = `${sum.detection_overview?.detection_frame_percentage || 0}% frames active`;

    classSummaryTableBody.innerHTML = "";
    const classes = ["front", "rear", "side"];
    classes.forEach((cls) => {
      const stat = sum.class_statistics?.[cls] || {
        frames_with_class: 0,
        total_detections: 0,
        avg_confidence: 0,
        max_confidence: 0,
      };
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong class="pill pill-${cls}">${cls.toUpperCase()}</strong></td>
        <td>${stat.frames_with_class}</td>
        <td><strong>${stat.total_detections}</strong></td>
        <td>${stat.avg_confidence.toFixed(4)}</td>
        <td>${stat.max_confidence.toFixed(4)}</td>
      `;
      classSummaryTableBody.appendChild(tr);
    });
  }

  // --- MODAL VIEWER ---
  btnViewSummaryMd.addEventListener("click", () => {
    if (!lastCompletedSummary) return;
    mdModalContent.textContent = JSON.stringify(lastCompletedSummary, null, 2);
    mdModal.style.display = "flex";
  });
  btnCloseModal.addEventListener("click", () => {
    mdModal.style.display = "none";
  });
  mdModal.addEventListener("click", (e) => {
    if (e.target === mdModal) mdModal.style.display = "none";
  });

  // --- SINGLE-IMAGE QUICK TEST ---
  let activeImageFile = null;
  imageDropzone.addEventListener("click", () => imageFileInput.click());
  imageFileInput.addEventListener("change", (e) => {
    if (e.target.files?.length > 0) {
      activeImageFile = e.target.files[0];
      btnTestImage.disabled = false;
      imageDropzone.querySelector(".dropzone-prompt").innerHTML = `Selected: <strong>${activeImageFile.name}</strong>`;
    }
  });

  btnTestImage.addEventListener("click", () => {
    if (!activeImageFile) return;
    btnTestImage.disabled = true;

    const formData = new FormData();
    formData.append("image", activeImageFile);
    formData.append("conf", imgConfRange.value);

    fetch("/api/predict_image", {
      method: "POST",
      body: formData,
    })
      .then((r) => r.json())
      .then((data) => {
        btnTestImage.disabled = false;
        if (data.annotated_image_base64) {
          emptyImageState.style.display = "none";
          imageResultContainer.style.display = "block";
          annotatedImagePreview.src = data.annotated_image_base64;

          imageStatsFooter.innerHTML = `
            <div class="stat-card">
              <div class="stat-label">Inference Time</div>
              <div class="stat-value highlight-cyan">${data.inference_time_ms} ms</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Total Detections</div>
              <div class="stat-value highlight-amber">${data.total_detections}</div>
            </div>
          `;
        } else {
          alert("Image inference failed: " + (data.error || "Unknown error"));
        }
      })
      .catch((err) => {
        btnTestImage.disabled = false;
        alert("Inference error: " + err);
      });
  });

  // --- BENCHMARK DATA ---
  function loadBenchmarkData() {
    fetch("/api/benchmark")
      .then((r) => r.json())
      .then((data) => {
        if (data.metrics?.confusion_matrix) {
          // Plots and numbers are linked statically
        }
      })
      .catch(() => {});
  }

  // --- HISTORY RUNS ---
  function loadHistoryRuns() {
    historyListContainer.innerHTML = '<p class="text-muted">Loading test history...</p>';

    fetch("/api/runs")
      .then((r) => r.json())
      .then((data) => {
        const runs = data.runs || [];
        if (runs.length === 0) {
          historyListContainer.innerHTML = '<p class="text-muted">No past video runs recorded yet.</p>';
          return;
        }

        historyListContainer.innerHTML = "";
        runs.forEach((r) => {
          const item = document.createElement("div");
          item.className = "history-item";
          const dets = r.summary?.detection_overview?.total_detections || 0;
          const fps = (r.summary?.performance?.average_inference_fps || 0).toFixed(1);
          const dateStr = new Date(r.created_at * 1000).toLocaleString();

          item.innerHTML = `
            <div>
              <strong style="color: #60a5fa;">${r.run_id}</strong>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
                ${dateStr} • ${dets} detections • ${fps} FPS
              </div>
            </div>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn-secondary btn-sm btn-replay-run" data-video="${r.video_url}">▶ Replay</button>
            </div>
          `;
          historyListContainer.appendChild(item);
        });

        document.querySelectorAll(".btn-replay-run").forEach((btn) => {
          btn.addEventListener("click", (e) => {
            const vUrl = e.currentTarget.dataset.video;
            // Switch to video tab and play
            navTabs[0].click();
            emptyVideoState.style.display = "none";
            videoPlayerContainer.style.display = "block";
            videoSource.src = vUrl;
            processedVideoPlayer.load();
            processedVideoPlayer.play();
          });
        });
      })
      .catch(() => {
        historyListContainer.innerHTML = '<p class="text-muted">Failed to load history.</p>';
      });
  }

  btnRefreshHistory.addEventListener("click", loadHistoryRuns);
});
