/* label animations, upon active */
$(document).ready(startAnimations);

function startAnimations() {
    $(".inputField").on("focus", function() {
        $(this).next(".inputLabel").slideDown(300);
    });
    $(".inputField").on("blur", function() {
        $(this).next(".inputLabel").slideUp(300);
    });
}

/* we only accept numbers and letters for usernames/pws */
function isAlphaNumeric(str) {
    var len = str.length;

    for (var i = 0; i < len; i++) {
        code = str.charCodeAt(i);
        if (!(code > 47 && code < 58) && // 0-9
            !(code > 64 && code < 91) && // A-Z
            !(code > 96 && code < 123)) { // a-z
            return false;
        }
    }
    return true;
}

/*  username must be between min and max number of characters long */
function validate_uid(uid, min, max) {
    var username = uid.value.toString();

    if (!isAlphaNumeric(username)) {
        return false;
    }
    if (username.length <= max && username.length >= min) {
        return true;
    }
    return false;
}

/*  password must contain between min and max number of characters long, and it 
    must contain at least 1 number */
function validate_pw(pw, min, max) {
    var pass = pw.value.toString();

    if (!isAlphaNumeric(pass)) {
        return false;
    }

    if (pass.length >= max || pass.length <= min) {
        return false;
    }

    var containsNum = false;
    for (var i = 0, len = pass.length; i < len; i++) {
        if (!isNaN(parseFloat(pass.substring(i, i + 1))) && isFinite(pass.substring(i, i + 1)))
            containsNum = true;
    }
    return containsNum;
}

function validateEmail(em) {
    var email = em.value.toString();
    var len = email.length;

    for (var i = 0; i < len; i++) {
        code = email.charCodeAt(i);
        if (!(code > 47 && code < 58) && // 0-9
            !(code > 64 && code < 91) && // A-Z
            !(code > 96 && code < 123) && // a-z
            !(code === 46 || code === 64)) { // . and @
            return false;
        }
    }
    return true;
};

function validate_signup(email, uid, pw, min, max) {
    // email should be auto-validated by the "email" field
    // all fields are required
    var uid_okay = validate_uid(uid, min, max);
    var pw_okay = validate_pw(pw, min, max);
    var email_okay = validateEmail(email);

    if (!email_okay) {
        alert("Please select a valid email.");
        return false;
    }
    if (!uid_okay) {
        if (!pw_okay)
            alert("Please select a valid username and password.");
        else
            alert("Please select a valid username.");
    } else if (!pw_okay)
        alert("Please select a valid password.");

    if (uid_okay && pw_okay && email_okay) {
        return true;
    }
    return false;
}

function signup(form) {
    var uid = form.elements["uid"];
    var password = form.elements["password"];
    var email = form.elements["email"];

    if (!validate_signup(email, uid, password, 4, 12))
        return false;

    var formData = new formData();

    formData.append('uid', uid);
    formData.append('password', password);
    formData.append('email', email);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/signup');

    xhr.send(formData);
    return true;
}

function signin(form) {
    var uid = form.elements["uid"];
    var password = form.elements["password"];

    var formData = new formData();
    formData.append('uid', uid);
    formData.append('password', password);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/signin');

    xhr.send(formData);
}