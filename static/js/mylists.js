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
    
    var url = $(this).first("input[type='hidden']").val();
    var listid = url.slice(9);
    var perm = $(tools).find("input[type='hidden']").val();
    // wipe out hidden input so don't have to keep repeating script
    if(perm != undefined)
    {
        console.log(perm);

        var permBox = $(tools).find(".permissions");
        if(perm==="own")
        {
            $(tools).css("height","8em");
            $(permBox).css("height","6em");
            $(permBox).html("You are the owner of this list.");
        }
        else if(perm==="edit")
        {
            $(permBox).html("You may view and edit this list.");
            $(tools).css("height","8em");
            $(permBox).css("height","6em");
            $(permBox).html("You are the owner of this list.<br>Add editor.<br>Add viewer.<br>Delete list.");
        }
        else if(perm==="view")
        {
            $(permBox).html("You may view this list.");
        }
    }
}
function hideToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.hide();
}