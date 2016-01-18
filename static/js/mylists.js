var listid = 0;
$(document).ready(function()
{
    
    // expands preview on click (should I make it click?) over url
    $(".listBlock2").on("mouseenter", ".list", previewLink);
    
    // view toolbox on hover
    $(".listWrapper").on("mouseenter", showToolbox);
    
    // hide toolbox on leave
    $(".listWrapper").on("mouseleave", hideToolbox);
    
    // copy url to clipboard upon clicking in it
    $(".toolbox").on("click", "input", useButtons);
    
    // focusout saves permissions and checks for delete
    $(".toolbox").on("focusout", "input", saveSettings);
    
});
function previewLink()
{
    var url = $(this).find("input").next().attr("value");
    var preview = $(this).parent().parent().parent().parent().find("iframe");
    // don't want the preview to keep flickering if same link
    if($(preview).attr("src") !== url)
    {
        $(preview).attr("src",url);
    }
}
function showToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.show();
    
    var url = $(this).find(".list input").val();
    // cut out "/list/"
    listid = url.slice(6);
    
    var perm = $(tools).find("input[type='hidden']").val();
    console.log(perm);
    
    // wipe out hidden input so don't have to keep repeating script
    if(perm != undefined)
    {
        if(perm==="own")
        {
            $(tools).html('<div class="icon-container"> <div class="icon-share icon"></div> <div class="icon-view icon"></div> <div class="icon-edit icon"></div> <div class="icon-link icon"></div> <div class="icon-trash icon"></div> </div> <div class="permissions"> <div class="line">You are the owner of this list.</div> <input class="editors" id="view" type="text"> <input class="editors" id="edit" type="text"> <input class="editors" id="url" type="text" value=' + url + '> <input class="editors" id="delete" type="text" placeholder="Type &quot;delete&quot; to delete list."> </div>');
            $(tools).css("height","11em");
        }
        else if(perm==="edit")
        {
            $(tools).html('<div class="icon-container"> <div class="icon-share icon"></div> <div class="icon-link-2 icon"></div> </div> <div class="permissions"> <div class="line">You may edit and view this list.</div> <input class="editors" id="url" type="text" value=' + url + '> </div>');
            $(tools).css("height","5em");
        }
        else if(perm==="view")
        {
            $(tools).html('<div class="icon-container"> <div class="icon-share icon"></div> <div class="icon-link-2 icon"></div> </div> <div class="permissions"> <div class="line">You may view this list.</div> <input class="editors" id="url" type="text" value=' + url + '> </div>');
            $(tools).css("height","5em");
        }
    }
}
function hideToolbox()
{
    var tools = $(this).find(".toolbox");
    tools.hide();
}
function useButtons()
{
    // url gets copied to clipboard every time
    if($(this).attr("id")==="url")
    {
        $(this).select();
        document.execCommand("copy");
        alert("Link copied to clipboard!");
    }
}
function saveSettings()
{
    if($(this).attr("id")==="delete")
    {
        if($(this).val()==="delete")
        {
            deleteList(listid);
        }
    }
    else if($(this).attr("id")==="view")
    {
    }
    else if($(this).attr("id")==="edit")
    {
    }
}
function deleteList(listid)
{
    // verify once more that the user is indeed the owner of the list
    var isOwner = false;
    $.ajax({
        url: "/api/getpermissions",
        method: 'POST',
        data: {
            listid: listid,
        },
        success: function(data, status, jqxhr){
            isOwner = true;
        }
    })
    if(isOwner)
    {
        if (confirm("Are you sure you want to permanently delete your list?"))
        {
            $.ajax({
                url: "/api/deletelist",
                method: 'POST',
                data: {
                    listid: listid,
                },
                success: function(data, status, jqxhr){
                    alert("You have deleted list " + listid);
                    location.reload(true); // reload from server not cache
                }
            });
        }
    }
}