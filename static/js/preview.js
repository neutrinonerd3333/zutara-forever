/* This is an extremely slimmed down version of home.js that will
 * only allow users to preview lists, and not perform any actions on them.
 * It should be quicker to load by a lot
 */
$(document).ready(function()
{
    // creates list on first serious attempt at making a list
    // clicking the down arrow will show attributes
    // clicking the up arrow will hide the attributes
    $(".list").on("click", "img", function()
    {
        var file = $(this).attr("src");
        
        // if currently up arrow, click should hide attributes and switch
        // to up arrow
        if(file==="/static/img/up.svg")
        {
            $(this).next(".attributes").slideUp(500);
            $(this).attr("src","/static/img/down.svg");
            $(this).prev(".itemTitle").find("input").css("border-radius","20px");
        }
        // if currently down arrow, click should show attributes and switch
        // to up arrow
        else
        {
            $(this).next(".attributes").slideDown(500);
            $(this).attr("src","/static/img/up.svg");
            $(this).prev(".itemTitle").find("input").css("border-radius","20px 20px 0 0");
        }
        
    });
});