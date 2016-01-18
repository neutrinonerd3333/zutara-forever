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
    if(css.charAt(0) === "0") {
        return false;
    }
    else {
        return true;
    }
}

$(document).ready(function()
{
    $(".list").on("click", ".icon-down", function()
    {
        // if currently up arrow, click should hide attributes and switch
        // to up arrow
        if(isArrowUp($(this))){
            $(this).next(".attributes").slideUp(500);
            $(this).css("background-position","0 0");
            $(this).prev(".itemTitle").find("input").css("border-radius","20px");

            var nums = $(this).closest(".listItem").find(".attribute").length;
            // if more than one entry, check if any are empty
            if(nums > 1)
            {
                // find attributes following arrow img
                var atts = $(this).next(".attributes").find(".attribute");
                // find the input fields under the key and value divs
                var keys = $(this).next(".attributes").find(".key :input");
                var vals = $(this).next(".attributes").find(".value :input");
                
                for(var i = atts.length-1; i >= 0; i--)
                {
                    // get values of each attribute
                    key = $(keys[i]).val();
                    value = $(vals[i]).val();
                    // check if whole row empty
                    if(key.length===0 && value.length===0)
                    {
                        $(atts[i]).remove();
                    }
                }
            }
        }
        // if currently down arrow, click should show attributes and switch
        // to up arrow
        else {
            $(this).next(".attributes").slideDown(500);
            $(this).css("background-position","-1.5em 0");
            $(this).prev(".itemTitle").find("input").css("border-radius","20px 20px 0 0");
        }  
    });
    // clicking heart will add a vote to the item (or remove it if existing)
    $(".list").on("click", ".icon-heart", function(){
        alert("You clicked the heart!");
        $(this).css("background-position","-10.5em 0");
        var item = $(this).closest(".listItem");
        var eind = $(".list .listItem").index(item);
        $.ajax({
            url: "/api/vote",
            method: 'POST',
            data: {
                listid: listid,
                entryid: eind,
                vote: 1
            },
            success: function(data, status, jqxhr){
                console.log("Current score is " + score);
            }
        });
    });
});