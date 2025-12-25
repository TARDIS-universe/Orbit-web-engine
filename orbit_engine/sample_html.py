SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
body { background: #0f172a; color: #e2e8f0; padding: 16px; }
h1 { color: #38bdf8; }
button.primary { background: #38bdf8; color: #0f172a; padding: 8px; }
input { padding: 6px; border-radius: 6px; border: 1px solid #1f2937; background: #111827; color: #e2e8f0; }
div { padding: 8px 0; }
</style>
<script>
function greet() {
  const name = getText('#name');
  const message = 'Hello, ' + (name || 'friend') + '!';
  setText('#message', message);
  setStyle('#message', 'color', '#38bdf8');
  setCookie('lastGreeting', message);
  fetch('https://orbit.local/hello');
}
onClick('#greet', greet);
</script>
</head>
<body>
  <h1>Orbit Web Engine</h1>
  <p>Small HTML/CSS/JS renderer built with Tkinter.</p>
  <div>
    <input id="name" value="Explorer" />
    <button id="greet" class="primary">Greet</button>
  </div>
  <p id="message">Click the button to say hello.</p>
</body>
</html>
"""
