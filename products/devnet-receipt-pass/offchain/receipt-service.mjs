#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const RPC_URL = process.env.SOLANA_DEVNET_RPC_URL || "https://api.devnet.solana.com";
const OUT =
  process.argv[2] ||
  "pilots/devnet-receipt-pass-test/devnet/devnet-read-proof.json";

const sampleEvent = {
  product_id: "devnet-receipt-pass",
  event_type: "factory_validation_receipt_created",
  event_version: 1,
  actor: "factory-validation-runner",
  authority_boundary: "read_only_devnet_no_signing_no_write",
};

async function rpc(method, params = []) {
  const response = await fetch(RPC_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: `drp-${method}`,
      method,
      params,
    }),
  });
  if (!response.ok) {
    throw new Error(`${method} HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload.error) {
    throw new Error(`${method} RPC error: ${JSON.stringify(payload.error)}`);
  }
  return payload.result;
}

function sha256(value) {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

async function main() {
  const latestBlockhash = await rpc("getLatestBlockhash", [
    { commitment: "processed" },
  ]);
  const epochInfo = await rpc("getEpochInfo", [{ commitment: "processed" }]);
  const clusterNodes = await rpc("getClusterNodes", []);

  const observedAt = new Date().toISOString();
  const proofInput = {
    sampleEvent,
    rpc_url: RPC_URL,
    latest_blockhash: latestBlockhash.value.blockhash,
    last_valid_block_height: latestBlockhash.value.lastValidBlockHeight,
    epoch: epochInfo.epoch,
    slot: epochInfo.absoluteSlot,
    observed_at: observedAt,
  };

  const receiptId = `drp_${sha256(proofInput).slice(0, 24)}`;
  const proof = {
    $schema: "https://overkill-factory.dev/schemas/devnet-read-proof.schema.json",
    result: "PASS",
    receipt_id: receiptId,
    proof_hash: sha256({ receiptId, proofInput }),
    observed_at: observedAt,
    devnet_rpc: {
      url: RPC_URL,
      methods: ["getLatestBlockhash", "getEpochInfo", "getClusterNodes"],
      latest_blockhash: latestBlockhash.value.blockhash,
      last_valid_block_height: latestBlockhash.value.lastValidBlockHeight,
      epoch: epochInfo.epoch,
      slot: epochInfo.absoluteSlot,
      sampled_node_count: Array.isArray(clusterNodes) ? clusterNodes.length : 0,
    },
    event: sampleEvent,
    boundaries: {
      signing: "forbidden",
      devnet_write: "forbidden",
      mainnet_write: "forbidden",
      secret_access: "forbidden",
      deploy: "forbidden",
    },
  };

  const outPath = resolve(OUT);
  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, `${JSON.stringify(proof, null, 2)}\n`, "utf8");
  console.log(JSON.stringify({ result: "PASS", out: OUT, receipt_id: receiptId }, null, 2));
}

main().catch(async (error) => {
  const observedAt = new Date().toISOString();
  const proof = {
    $schema: "https://overkill-factory.dev/schemas/devnet-read-proof.schema.json",
    result: "FAIL",
    observed_at: observedAt,
    error: error.message,
    boundaries: {
      signing: "forbidden",
      devnet_write: "forbidden",
      mainnet_write: "forbidden",
      secret_access: "forbidden",
      deploy: "forbidden",
    },
  };
  const outPath = resolve(OUT);
  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, `${JSON.stringify(proof, null, 2)}\n`, "utf8");
  console.error(JSON.stringify({ result: "FAIL", out: OUT, error: error.message }, null, 2));
  process.exit(1);
});
