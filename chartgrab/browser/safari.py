"""Capture a snapshot from an open Safari tab on macOS via JavaScript for Automation (JXA).

Requirements: macOS, Safari > Settings > Advanced > "Show features for web developers", then
Develop > "Allow JavaScript from Apple Events". The tab is read in place: nothing is
clicked, focused, reloaded or navigated. Exactly one window whose current tab URL matches
must exist; hidden, minimised or occluded duplicates are ignored when one visible match remains.
"""
from __future__ import annotations

import json
import subprocess
from typing import Optional

from ..snapshot import collector_expression

_JXA = r'''
function run(argv) {
  const expr = argv[0], needle = argv[1];
  const safari = Application('Safari');
  if (!safari.running()) return JSON.stringify({error: 'SAFARI_NOT_RUNNING'});
  const matches = [];
  for (const w of safari.windows()) {
    try {
      const tab = w.currentTab();
      if (String(tab.url()).indexOf(needle) === -1) continue;
      let vis = 'unknown';
      try { vis = safari.doJavaScript('document.visibilityState', {in: tab}); } catch (_) {}
      matches.push({w, tab, visible: w.visible() && !w.miniaturized() && vis === 'visible'});
    } catch (_) {}
  }
  let pick = matches.length === 1 ? matches : matches.filter(m => m.visible);
  if (pick.length !== 1)
    return JSON.stringify({error: 'TAB_NOT_UNIQUE', matches: matches.length, visible: pick.length});
  const out = safari.doJavaScript('JSON.stringify(' + expr + ')', {in: pick[0].tab});
  return out;
}
'''


def capture_safari(url_substring: str, options: Optional[dict] = None, timeout: float = 30) -> dict:
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", _JXA, collector_expression(options), url_substring],
        capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript failed")
    data = json.loads(proc.stdout)
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(json.dumps(data))
    return data
