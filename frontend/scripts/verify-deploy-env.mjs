import { pathToFileURL } from 'node:url';
import { allocationUrl } from '../src/api.js';

export function checkDeploymentOrigin(base) {
  if (!base) throw new Error('Set VITE_API_BASE_URL to the existing working HTTPS API origin before deployment.');
  const endpoint = allocationUrl(base);
  if (/REPLACE|\.invalid\b|example\./i.test(endpoint)) throw new Error('Replace the placeholder API origin before deployment.');
  return endpoint;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  checkDeploymentOrigin(process.env.VITE_API_BASE_URL);
  console.log('Deployment API origin is configured (public build-time setting).');
}
