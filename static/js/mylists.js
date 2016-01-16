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
    
    var url = $(this).find("input[type='hidden']").val();
    var listid = url.slice(9);
    var perm = getPermissions(listid);
    console.log(perm);
}
function hideToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.hide();
}
function displayPermissions()
{
    var permBox = $(".permissions")
}
function getPermissions(listid)
{
    $.ajax({
        url: "/api/getpermissions",
        method: 'POST',
        data: {
            listid: listid,
        },
        success: function(data, status, jqxhr){
            console.log(data)
        }
    })
}