---
layout: default
---

I **should** _find_ ~~some~~ `junk`.

<p>Jim Graham</p>
<p id="email"></p>

<script>
    // Obfuscated parts of the email
    var user = "jim";
    var domain = "pobox";
    var tld = "com";

    // Combine them to form the email address
    var email = user + "@" + domain + "." + tld;
    var long_email = user + " @ " + domain + " . " + tld

    // Insert email into the paragraph element
    document.getElementById("email").innerHTML = '<a href="mailto:' + email + '">' + long_email + '</a>';
</script>
