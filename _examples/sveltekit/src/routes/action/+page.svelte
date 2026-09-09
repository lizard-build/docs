<script>let {form}= $props();</script><p id="result">{form?.message || "ready"}</p><form method="POST"><input name="message" value="action-ok"/><button>Send</button></form>
