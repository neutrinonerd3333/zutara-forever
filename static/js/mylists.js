$(document).ready(function()
{
    
    // expands preview on click (should I make it click?) over url
    $(".listBlock2").on("mouseenter", ".list", previewLink);
    
    // view toolbox on hover
    $(".listWrapper").on("mouseenter", showToolbox);
    
    // hide toolbox on leave
    $(".listWrapper").on("mouseleave", hideToolbox);
    
    // copy url to clipboard upon clicking in it
    $(".toolbox").on("click", "input", function(){
        $(this).select();
        document.execCommand("copy");
        alert("Link copied to clipboard!");
    });
    
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
        else
        {
            $(this).next(".attributes").slideDown(500);
            $(this).attr("src","/static/img/up.svg");
            $(this).prev(".itemTitle").find("input").css("border-radius","20px 20px 0 0");
        }
        
    });
    
    // clicking minus will delete the current entry
    $(".list").on("click", ".minus", function()
    {
        $(this).closest(".attribute").remove();
    });
});
function previewLink()
{
    var url = $(this).find("input").attr("value");
    $(this).parent().parent().parent().parent().find("iframe").attr("src",url);
}
function showToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.show();
}
function hideToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.hide();
}