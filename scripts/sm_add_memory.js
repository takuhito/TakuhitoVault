#!/usr/bin/env node
"use strict";

// Minimal MCP client over stdio to call supermemory.ai addMemory tool via mcp-remote
// Usage:
//   echo "content" | node scripts/sm_add_memory.js --project NotionWorkflowTools
//   node scripts/sm_add_memory.js --project NotionWorkflowTools --content "text here"

const { spawn } = require("child_process");

function parseArgs(argv) {
  const args = { project: process.env.X_SM_PROJECT || "NotionWorkflowTools", content: null, title: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--project" && argv[i + 1]) { args.project = argv[++i]; continue; }
    if (a === "--content" && argv[i + 1]) { args.content = argv[++i]; continue; }
    if (a === "--title" && argv[i + 1]) { args.title = argv[++i]; continue; }
  }
  return args;
}

async function readStdin() {
  return new Promise((resolve) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => data += chunk);
    process.stdin.on("end", () => resolve(data));
    if (process.stdin.isTTY) resolve("");
  });
}

function nowIso() {
  return new Date().toISOString();
}

async function main() {
  const opts = parseArgs(process.argv);
  const stdinText = await readStdin();
  const content = (opts.content && opts.content.length > 0) ? opts.content : stdinText;
  if (!content || content.trim().length === 0) {
    console.error("[sm_add_memory] No content provided.");
    process.exit(2);
  }

  const headerArg = `x-sm-project:${opts.project}`;
  const child = spawn("npx", ["-y", "mcp-remote@latest", "https://api.supermemory.ai/mcp", "--header", headerArg], {
    stdio: ["pipe", "pipe", "pipe"]
  });

  child.stderr.on("data", (d) => {
    // forward logs to stderr
    process.stderr.write(d);
  });

  let nextId = 1;
  function send(msg) {
    child.stdin.write(JSON.stringify(msg) + "\n");
  }

  const initId = nextId++;
  const callId = nextId++;
  const initMsg = {
    jsonrpc: "2.0",
    id: initId,
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "sm_add_memory", version: "1.0.0" }
    }
  };

  const payload = {
    thingToRemember: content,
    // Optional metadata; server may ignore unknown fields
    source: "auto-save",
    timestamp: nowIso()
  };

  const callMsg = {
    jsonrpc: "2.0",
    id: callId,
    method: "tools/call",
    params: {
      name: "addMemory",
      arguments: payload
    }
  };

  let initialized = false;
  let done = false;
  let buffer = "";
  child.stdout.setEncoding("utf8");
  child.stdout.on("data", (chunk) => {
    buffer += chunk;
    let idx;
    while ((idx = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 1);
      if (!line.trim()) continue;
      let msg;
      try { msg = JSON.parse(line); } catch (e) { continue; }
      if (msg.id === initId && msg.result && !initialized) {
        initialized = true;
        send(callMsg);
      } else if (msg.id === callId) {
        done = true;
        if (msg.error) {
          console.error(`[sm_add_memory] Error: ${JSON.stringify(msg.error)}`);
          process.exitCode = 1;
        } else {
          console.log("[sm_add_memory] Saved to supermemory.ai");
        }
        child.kill("SIGINT");
      }
    }
  });

  child.on("exit", (code) => {
    if (!done && code !== 0) {
      console.error(`[sm_add_memory] mcp-remote exited with code ${code}`);
      process.exit(code || 1);
    } else if (!done) {
      // graceful exit without response
      process.exit(0);
    }
  });

  // Kick off initialize after small delay to ensure listeners are ready
  setTimeout(() => send(initMsg), 50);
}

main().catch((e) => {
  console.error("[sm_add_memory] Fatal:", e);
  process.exit(1);
});


