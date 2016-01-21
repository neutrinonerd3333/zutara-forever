var listid = 0;
$(document).ready(function() {

    // expands preview on click (should I make it click?) over url
    $(".listBlock2").on("mouseenter", ".mylist", previewLink);

    // view toolbox on hover
    $(".listWrapper").on("mouseenter", showToolbox);

    // hide toolbox on leave
    $(".listWrapper").on("mouseleave", hideToolbox);

    // copy url to clipboard upon clicking in it
    $(".toolbox").on("click", "input", useButtons);

    // focusout saves permissions and checks for delete
    $(".toolbox").on("focusout", "input", saveSettings);

});

function previewLink() {
    var url = $(this).find("input").next().attr("value");
    var preview = $(this).parent().parent().parent().parent().find("iframe");
    // don't want the preview to keep flickering if same link
    if ($(preview).attr("src") !== url) {
        $(preview).attr("src", url);
    }
}

function showToolbox(perm) {
    var tools = $(this).find(".toolbox");
    var permInput = $(tools).find("input");
    tools.show();

    $(this).find(".mylist").css("background-color", "#AEF");
    var url = $(this).find(".mylist input").val();
    var n = url.indexOf('/list/');
    // cut out "/list/"
    listid = url.slice(n + 6);
    if($(permInput).val()===''){
        console.log(listid);
        $.ajax({
            data: {
                listid: listid,
            },
            url: "/api/getpermissions",
            method: 'POST',
            success: function(data, status, jqxhr) {
                // logged in if true, guest if false
                var perm = data.permission;
                $(permInput).val(perm);

                if (perm === "own") {
                    $(tools).html('<div class="icon-container"> <div class="icon-share"></div>  <div class="icon-edit"></div> <div class="icon-view"></div> <div class="icon-link"></div> <div class="icon-trash"></div> </div> <div class="permissions"> <div class="line">You are the owner of this list.</div> <input class="editors" id="edit" placeholder="Editors" type="text"> <input class="editors" id="view" placeholder="Viewers" type="text"> <input class="editors" id="url" type="text" value=' + url + '> <input class="editors" id="delete" type="text" placeholder="Type &quot;delete&quot; to delete list."> </div>');
                    $(tools).css("height", "11em");
                } else if (perm === "edit") {
                    $(tools).html('<div class="icon-container"> <div class="icon-share"></div> <div class="icon-link-2"></div> </div> <div class="permissions"> <div class="line">You may edit and view this list.</div> <input class="editors" id="url" type="text" value=' + url + '> </div>');
                    $(tools).css("height", "5em");
                } else if (perm === "view") {
                    $(tools).html('<div class="icon-container"> <div class="icon-share"></div> <div class="icon-link-2"></div> </div> <div class="permissions"> <div class="line">You may view this list.</div> <input class="editors" id="url" type="text" value=' + url + '> </div>');
                    $(tools).css("height", "5em");
                }
            }
        });
    }
}

function hideToolbox() {
    $(this).find(".mylist").css("background-color", "#CEF");
    var tools = $(this).find(".toolbox");
    tools.hide();
}

function useButtons() {
    // url gets copied to clipboard every time
    if ($(this).attr("id") === "url") {
        $(this).select();
        document.execCommand("copy");
        alert("Link copied to clipboard!");
    }
}

function saveSettings() {
    if ($(this).attr("id") === "delete") {
        if ($(this).val() === "delete") {
            console.log("deleted")
            deleteList(listid);
        }
    } else if ($(this).attr("id") === "view") {} else if ($(this).attr("id") === "edit") {}
}

function deleteList(listid) {
    // verify permission rank
    var isOwner = false;
    $.ajax({
        url: "/api/getpermissions",
        method: 'POST',
        data: {
            listid: listid,
        },
        success: function(data, status, jqxhr) {
            var perm = data.permission;
            if(perm==='own') {
                if (confirm("Are you sure you want to permanently delete your list?")) {
                    $.ajax({
                        url: "/api/deletelist",
                        method: 'POST',
                        data: {
                            listid: listid,
                        },
                        success: function(data, status, jqxhr) {
                            alert("You have deleted list " + listid);
                            location.reload(true); // reload from server not cache
                        }
                    });
                }
            }
            // else no permission to delete
            // and can only delete self
            else {
                if (confirm("Are you sure you want to permanently remove yourself from this list?")) {
                    $.ajax({
                        url: "/api/setpermissions",
                        method: 'POST',
                        data: {
                            listid: listid,
                            permission: perm
                        },
                        success: function(data, status, jqxhr) {
                            alert("You have deleted list " + listid);
                            location.reload(true); // reload from server not cache
                        }
                    });
                }
            }
        }
    });
}