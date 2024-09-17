function obfuscateEmail() {
    var link = document.getElementById("contact-link");
    var email = link.href.replace("mailto:", "");
    var obfuscated = "";

    for (var i = 0; i < email.length; i++) {
        obfuscated += "&#" + email.charCodeAt(i) + ";";
    }

    link.href = "mailto:" + obfuscated;
}