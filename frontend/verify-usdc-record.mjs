import { verifyRecord } from './usdc-protocol.mjs'
let input = ''
for await (const chunk of process.stdin) input += chunk
try {
  const { config, record } = JSON.parse(input)
  process.stdout.write(JSON.stringify({ digest: verifyRecord(config, record) }))
} catch {
  process.stderr.write('Invalid authorization signatures')
  process.exitCode = 1
}
