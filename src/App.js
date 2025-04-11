import React, { useState, useEffect, useCallback } from "react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";

export default function App() {
  const [files, setFiles] = useState([]);
  const [fileNames, setFileNames] = useState([]);
  const allowedExtensions = [".js", ".py", ".cpp", ".java", ".html", ".css"];
  const [extensions, setExtensions] = useState("Allowed extensions: " + allowedExtensions.join(", "));
  const [validSelection, setValidSelection] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("Preparing magic...");
  const [progressPercent, setProgressPercent] = useState(0);
  const [generationId, setGenerationId] = useState(null); // 🪄 Track current generation task
  const emojiList = ["🧚‍♀️", "🐉", "📜", "✨", "🪄", "🌸", "📦", "⚙️", "🧠"];
  const [currentEmoji, setCurrentEmoji] = useState(emojiList[0]);
  const [batchSize, setBatchSize] = useState(20); // default is in the middle

  const API_BASE = process.env.REACT_APP_API_BASE_URL;

  const handleUpload = async () => {
    setIsLoading(true);
    // Start truly at 0%
    setProgressPercent(0);
    setLoadingStage("🧃 Preparing to process...");

    await new Promise((resolve) => setTimeout(resolve, 300));

    // Intermittent stage at 10%
    setLoadingStage("🌼 Reading your files...");
    setProgressPercent(10);

    await new Promise((resolve) => setTimeout(resolve, 400));

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      // Step 1: Splitting into batches
      setLoadingStage("🔍 Splitting into batches...");
      setProgressPercent(30);

      await new Promise((resolve) => setTimeout(resolve, 500)); // Small pause for animation effect

      // Step 2: Sending batches to AI
      setLoadingStage("📡 Sending batches to AI...");
      setProgressPercent(60);

      // 🌟 Get a unique generation ID from backend
      const idRes = await fetch(`${API_BASE}/generate-id`);
      const { generation_id } = await idRes.json();
      setGenerationId(generation_id);
      formData.append("generation_id", generation_id);

      formData.append("batch_size", batchSize);

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      // Handle cancellation or failure
      if (!response.ok || !result.success) {
        setIsLoading(false);
        setProgressPercent(0);

        if (result?.error === "Generation cancelled by user") {
          alert("❌ You cancelled the generation.");
        } else {
          console.error("Backend error:", result?.error || "Unknown error");
        }
        return;
      }

      // Step 3: Finalizing
      setLoadingStage("✨ Finalizing and rendering docs...");
      setProgressPercent(90);

      await new Promise((resolve) => setTimeout(resolve, 400)); // Optional pause for dramatic effect

      setProgressPercent(100);
      setIsLoading(false);

      const filenameParam = encodeURIComponent(files[0].name);
      const docURL = `${API_BASE}${result.htmlPath}?filename=${filenameParam}`;
      window.open(docURL, "_blank");

    } catch (err) {
      console.error("Upload failed:", err);
      setIsLoading(false);
    }
    setGenerationId(null);
    setProgressPercent(0);
  };

  useEffect(() => {
    if (!generationId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/generation-progress/${generationId}`);
        const data = await res.json();
        const status = data.status;

        if (status.startsWith("generating:")) {
          const percent = parseInt(status.split(":")[1]);
          setLoadingStage("📡 Generating AI descriptions...");
          setProgressPercent(percent);
        } else if (status === "done") {
          setProgressPercent(100);
          setLoadingStage("🎉 Finished! Opening docs...");
          clearInterval(interval);
          setTimeout(() => setIsLoading(false), 500);
        } else if (status === "cancelled") {
          clearInterval(interval);
          setIsLoading(false);
          alert("❌ Generation was cancelled.");
        }
      } catch (err) {
        console.error("Polling failed:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [generationId]);

  useEffect(() => {
    if (!isLoading) return;

    const interval = setInterval(() => {
      setCurrentEmoji((prevEmoji) => {
        const currentIndex = emojiList.indexOf(prevEmoji);
        const nextIndex = (currentIndex + 1) % emojiList.length;
        return emojiList[nextIndex];
      });
    }, 1000); // change every second (can tweak)

    return () => clearInterval(interval);
  }, [isLoading]);

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(droppedFiles);
    setFileNames(droppedFiles.map(file => file.name));

    const badFiles = droppedFiles.filter(file => {
      const ext = "." + file.name.split(".").pop().toLowerCase();
      return !allowedExtensions.includes(ext);
    });

    if (droppedFiles.length === 0) {
      setValidSelection(false);
      setExtensions("Allowed extensions: " + allowedExtensions.join(", "));
    } else if (badFiles.length > 0) {
      setValidSelection(false);
      setExtensions(
        `❌ Unsupported file extension(s): ${badFiles.map(f => "." + f.name.split(".").pop().toLowerCase()).join(", ")}`
      );
    } else {
      setValidSelection(true);
      const extList = droppedFiles.map(f => "." + f.name.split(".").pop().toLowerCase());
      setExtensions("📂 Selected file's extension: " + [...new Set(extList)].join(", "));

      // ✨ Simulate setting it to the file input visually
      const fileInput = document.querySelector('input[type="file"]');
      const dataTransfer = new DataTransfer();
      droppedFiles.forEach(file => dataTransfer.items.add(file));
      fileInput.files = dataTransfer.files;
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  return (
    <div className="min-h-screen bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-white flex flex-col">
      {/* 🌟 Title at the top */}
      <div className="w-full text-center p-6">
        <h1 className="text-4xl font-bold">✨ CodeScroll ✨</h1><br></br>
        <h2 className="text-2xl font-bold"> Your Code Documentation Generator </h2>
        <hr className="border-white border-2 opacity-30 mt-4" />
      </div>

      {/* 🧩 Centered content */}
      <div className="flex-grow flex items-center justify-center px-6">
        <div className="grid gap-6 w-full max-w-xl">
          <div className="flex items-center flex-wrap gap-4">
            <input
              type="file"
              multiple
              onChange={(e) => {
                const selectedFiles = Array.from(e.target.files);
                setFiles(selectedFiles);
                setFileNames(selectedFiles.map(file => file.name));

                const badFiles = selectedFiles.filter(file => {
                  const ext = "." + file.name.split(".").pop().toLowerCase();
                  return !allowedExtensions.includes(ext);
                });

                if (selectedFiles.length === 0) {
                  setValidSelection(false);
                  setExtensions("Allowed extensions: " + allowedExtensions.join(", "));
                } else if (badFiles.length > 0) {
                  setValidSelection(false);
                  setExtensions(`❌ Unsupported file extension(s): ${badFiles.map(f => "." + f.name.split(".").pop().toLowerCase()).join(", ")}`);
                } else {
                  setValidSelection(true);
                  const extList = selectedFiles.map(f => "." + f.name.split(".").pop().toLowerCase());
                  setExtensions("📂 Selected file's extension: " + [...new Set(extList)].join(", "));
                }
              }}
              className="file:bg-yellow-300 file:text-black file:font-semibold file:border-none file:px-4 file:py-2 file:rounded file:shadow-sm file:mr-4 file:cursor-pointer hover:file:bg-yellow-200 bg-white text-black rounded w-full"
            />
          </div>

          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="w-full text-center border-4 border-dashed rounded-lg p-4 bg-white/30 backdrop-blur-md hover:shadow-md transition-all duration-300 cursor-pointer border-pink-400 hover:border-purple-400 text-purple-800 font-medium animate-in fade-in zoom-in"
            style={{
              borderImage: "linear-gradient(90deg, #f472b6, #c084fc, #60a5fa) 1",
              borderImageSlice: 1,
              fontFamily: "'Comic Neue', cursive"
            }}
          >
            <div className="text-2xl animate-bounce mb-1">🌸✨🧺✨🌸</div>
            <div className="text-sm">Or drag and drop your files here</div>
          </div>

          <div
            className={`w-full rounded px-3 py-2 bg-gray-200 text-sm font-mono ${extensions.startsWith("❌") ? "text-red-600" : "text-black"
              }`}
          >
            {extensions.startsWith("📂") ? (
              <>
                <span className="text-blue-700 font-semibold">📂 Selected file's extension:</span>
                {extensions.replace("📂 Selected file's extension:", "")}
              </>
            ) : (
              extensions
            )}
          </div>

          <div className="magic-glow-border rounded-xl">
            <div className="bg-white/30 backdrop-blur-md px-2 py-1 rounded-lg shadow-inner text-black relative">
              <div className="text-s text-white text-center font-semibold leading-tight flex items-center justify-center gap-1">
                ✨ Batch-Size: {batchSize}

                {/* Info Button with group */}
                <div className="relative ml-2 group"
                >
                  {/* Blue info circle */}
                  <div
                    className="w-5 h-5 rounded-full bg-blue-500 text-white text-[10px] font-bold flex items-center justify-center cursor-pointer hover:scale-105 transition-all"
                    style={{ border: "2px dashed limegreen" }}
                  >
                    i
                  </div>

                  {/* Tooltip */}
                  <div
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-black bg-opacity-80 text-white text-xs px-3 py-2 rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-[9999]"
                    style={{
                      pointerEvents: "none", // prevent stealing hover
                      border: "1px dashed magenta"
                    }}
                  >
                    We use AI-generated descriptions to describe snippets of your code. For this, we send snippets of your code in batches to the AI. This bar controls how many snippets are sent to the AI at once. Lower values improve accuracy but take longer, while higher ones speed things up but can increase chances of inaccuracies.
                  </div>
                </div>
              </div>

              {/* Slider */}
              <input
                type="range"
                min="5"
                max="40"
                step="1"
                value={batchSize}
                onChange={(e) => setBatchSize(parseInt(e.target.value))}
                className="w-full appearance-none rounded-full mt-0.5 mb-0.5"
                style={{
                  height: "6px",
                  background: `linear-gradient(to right, #0ea5e9 0%, #f43f5e ${((batchSize - 5) / (40 - 5)) * 100
                    }%, #e5e7eb ${(batchSize - 5) / (40 - 5) * 100}%, #e5e7eb 100%)`,
                  boxShadow: "0 0 4px rgba(255, 255, 255, 0.3)",
                }}
              />

              {/* Descriptor */}
              <div className="text-[15px] text-white text-center italic leading-snug">
                {batchSize <= 10
                  ? "🎯 Accurate"
                  : batchSize >= 35
                    ? "⚡ Fast"
                    : "✨ Balanced"}
              </div>
            </div>
          </div>

          {/* Example using Tailwind + Poppins (Google Fonts)*/}
          <Button
            onClick={handleUpload}
            disabled={!validSelection}
            className="bg-yellow-300 !text-black hover:bg-yellow-200 font-poppins text-md hover:text-lg tracking-wide disabled:opacity-50 disabled:cursor-not-allowed"
          >
            🧙‍♂️ Generate Docs
          </Button>
        </div>
        {isLoading && (
          <div className="fixed inset-0 z-50 bg-black bg-opacity-60 flex items-center justify-center">
            <div className="bg-white rounded-xl shadow-2xl p-6 text-center w-96 relative animate-fadeInDown">
              <button
                className="absolute top-2 right-3 text-2xl text-red-500 hover:text-red-700 font-bold"
                onClick={() => {
                  setIsLoading(false);
                  if (generationId) {
                    fetch(`${API_BASE}/cancel-generation`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json"
                      },
                      body: JSON.stringify({ generation_id: generationId })
                    });
                  }
                }}
              >
                ×
              </button>

              <div className="text-3xl mb-4 animate-bounce transition-opacity duration-300 ease-in-out">
                {currentEmoji}
              </div>
              <p className="font-bold text-lg text-purple-700 mb-2">{loadingStage}</p>

              <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden mb-3">
                <div
                  className="h-full bg-gradient-to-r from-pink-400 via-purple-400 to-blue-400 transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                ></div>
              </div>

              <p className="text-sm text-gray-600 font-mono">
                Please sit tight while the documentation fairies do their thing 🧙‍♂️✨
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}