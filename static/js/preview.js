/* This is an extremely slimmed down version of home.js that will
 * only allow users to preview lists, and not perform any actions on them.
 * It should be quicker to load by a lot
 */
var pathname = window.location.pathname;
var n = pathname.search(/^\/preview\/.+/, pathname);
if (n === 0) {
    listid = pathname.slice(9);
}

function isArrowUp(icon) {
    var css = $(icon).css("background-position");
    // browser renders em into px, so 0 means left most = down arrow
    if (css.charAt(0) === "0") {
        return false;
    } else {
        return true;
    }
}

$(document).ready(function() {
    $(".list").on("click", ".icon-down", function() {
        // if currently up arrow, click should hide attributes and switch
        // to up arrow
        if (isArrowUp($(this))) {
            var attrs = $(this).next(".attributes");
            $(attrs).slideUp(500);
            $(this).css("background-position", "0 0");
            $(this).prev(".itemTitle").find("input").css("border-radius", "20px");
        }
        // if currently down arrow, click should show attributes and switch
        // to up arrow
        else {
            $(this).next(".attributes").slideDown(500);
            $(this).css("background-position", "-1.5em 0");
            $(this).prev(".itemTitle").find("input").css("border-radius", "20px 20px 0 0");
        }
    });
});