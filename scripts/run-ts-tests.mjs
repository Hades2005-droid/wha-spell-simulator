import { execFileSync } from 'node:child_process';
import process from 'node:process';

function stripTypesSupported() {
  try {
    execFileSync(process.execPath, ['--experimental-strip-types', '--version'], {
      stdio: 'ignore',
    });
    return true;
  } catch {
    return false;
  }
}

if (stripTypesSupported()) {
  execFileSync(
    process.execPath,
    ['--experimental-strip-types', '--test', 'tests/polymarketOracle.test.ts'],
    { stdio: 'inherit' },
  );
} else {
  process.stdout.write(
    'Skipping tests/polymarketOracle.test.ts: Node does not support --experimental-strip-types.\n',
  );
}
