var listid = 0;
var uid = "";
var perm = "";

$(document).ready(function() {

    // expands preview on click (should I make it click?) over url
    $(".listBlock2").on("mouseenter", ".mylist", previewLink);
    
    // view toolbox on clicking settings
    $(".listWrapper").on("click", ".icon-settings", openSettings);
    
    // hide toolbox on clicking back
    $(".listBlock3").on("click", ".icon-back", hideSettings);   

    // copy url to clipboard upon clicking in it
    $(".listBlock3").on("click", "input", useButtons);
    
    // on click delete, delete
    $(".listBlock3").on("click", ".icon-trash", buttonListener);

    // focusout saves permissions
    $(".listBlock3").on("focusout", "input", saveSettings);
    
    // change public permission on selecting different one
    $(".listBlock3").on("change", "select", setPublicPermission);
});

function previewLink() {
    var url = $(this).find("#preview").attr("value");
    var preview = $("iframe");
    // don't want the preview to keep flickering if same link
    if ($(preview).attr("src") !== url) {
        $(preview).attr("src", url);
    }
}

function openSettings() {
    // get the actual list entry following button
    var mylist = $(this).next();
    // permission in hidden input
    var title = $(mylist).find(".listTitle").text();
    // console.log(title);
    $(".listBlock3").find(".title").html(title);
    
    var permInput = $(mylist).find("#perm");
    var url = $(mylist).find("#url").val();
    
    // set values to corresponding list
    $(".listBlock3").find("#url").val(url);
    
    var n = url.indexOf('/list/');
    // cut out "/list/"
    listid = url.slice(n + 6);
    
    getPublicPermission(listid);
    getCurrentPerms(listid);
    
    // if first time loading settings, get permission
    // level from db
    if ($(permInput).val() === '') {
        // console.log(listid);
        $.ajax({
            data: {
                listid: listid,
            },
            url: "/api/getpermissions",
            method: 'POST',
            success: function(data, status, jqxhr) {
                var perm = data.permission;
        
                updatePerms(perm, permInput);
            }
        });
    }
    
    loadSettings();

    // actually show everything
    $(".listBlock2").fadeOut(500);
    $(".listBlock3").fadeIn(500);
}

function hideSettings() {
    $(".listBlock2").fadeIn(500);
    $(".listBlock3").fadeOut(500);
}

function useButtons() {
    // url gets copied to clipboard every time
    if ($(this).attr("id") === "url") {
        $(this).select();
        // no need to copy for now
        // document.execCommand("copy");
        // alert("Link copied to clipboard!");
    }
}

// this must be a .icon that was clicked
function buttonListener() {
    deleteList(listid);
}

function updatePerms(perm, permInput) {
    $(permInput).val(perm);
                
    var msg = ""
    // default delete msg is no permission
    // can only add permissions below your own
    if(perm==="own"){
        msg = "You are the owner of the list.";
        $(".listBlock3").find("#deletelist").html("Click trash to permanently delete list.");
        $(".listBlock3").find("#editors").prop('disabled', false);
        $(".listBlock3").find("#viewers").prop('disabled', false);
        $("select").prop('disabled', false);
    }
    else if(perm==="edit") {
        msg = "You can edit and view this list.";
        $(".listBlock3").find("#editors").prop('disabled', true);
        $(".listBlock3").find("#viewers").prop('disabled', true);
        $("select").prop('disabled', true);
    }
    else if(perm==="view") {
        msg = "You can view this list.";
        $(".listBlock3").find("#editors").prop('disabled', true);
        $(".listBlock3").find("#viewers").prop('disabled', true);
        $("select").prop('disabled', true);
    }
    else if(perm==="admin") {
        msg = "Tony why you snooping on people's lists?";
    }
    else {
        msg = "You do not have access to this list.";
    }
    $(".listBlock3").find("#permlvl").html(msg);
}

// select has 3 built in permission levels, so
// should be no exception here
function setPublicPermission() {
    var perm = $("select").val()
    
    $.ajax({
        url: "/api/setpubliclevel",
        method: "POST",
        data: {
            listid: listid,
            permission: perm
        },
        success: function(data, status, jqxhr) {
            console.log("success " + data);
            updatePublicPermission(perm) 
        }
    });
}

// disables or enables text box upon changing public permission
function updatePublicPermission(perm) {
    if(perm==="edit") {
        $(".listBlock3").find("#viewers").prop('disabled', true);
        $(".listBlock3").find("#editors").prop('disabled', true);
        $(".listBlock3").find("#viewers").attr('placeholder', "Anyone can view.");
        $(".listBlock3").find("#editors").attr('placeholder', "Anyone can edit.");
    }
    else if(perm==="view") {
        $(".listBlock3").find("#viewers").prop('disabled', true);
        $(".listBlock3").find("#editors").prop('disabled', false);
        $(".listBlock3").find("#viewers").attr('placeholder', "Anyone can view.");
        $(".listBlock3").find("#editors").attr('placeholder', "Oops! No editors yet.");
    }
    else if(perm==="none") {
        $(".listBlock3").find("#viewers").prop('disabled', false);
        $(".listBlock3").find("#editors").prop('disabled', false);
        $(".listBlock3").find("#viewers").attr('placeholder', "Oops! No viewers yet.");
        $(".listBlock3").find("#editors").attr('placeholder', "Oops! No editors yet.");
    }
}

function getPublicPermission(listid) {
    $.ajax({
        data: {
            listid: listid
        },
        url: "/api/getpubliclevel",
        method: "POST",
        success: function(data, status, jqxhr) {
            $(".listBlock3").find("select").val(data);
            updatePublicPermission(data)
        }
    });
}

function getCurrentPerms(listid) {
$.ajax({
        data: {
            listid: listid
        },
        url: "/api/permissions/listperms",
        method: "POST",
        success: function(data, status, jqxhr) {
            $("#editors").val(data.editors);
            $("#viewers").val(data.viewers);
        }
    });
}

function loadSettings() {
    $.ajax({
            data: {
                listid: listid
            },
            url: "api/permissions/listperms",
            method: 'POST',
            success: function(data, status, jqxhr) {
                var editors = data.editors;
                var viewers = data.viewers;
                
                if(editors.length > 0) {
                    $(".listBlock3").find("#editors").html(editors);
                }
                if(viewers.length > 0) {
                    $(".listBlock3").find("#viewers").html(viewers);
                }
            }
    });
}

function saveSettings() {
    // if user types in names, add them as viewers
    // or editors, as specified
    // names delimited by whitespace
    if ($(this).attr("id") === "viewers") {
        var all = $(this).val();
        var all = all.split();
        var n = all.length;
        for (var i = 0; i < n; i++) {
            setPermissions(listid, all[i], "view");
        }
    } else if ($(this).attr("id") === "editors") {
        var all = $(this).val();
        var all = all.split(" ");
        var n = all.length;

        for (var i = 0; i < n; i++) {
            // console.log(all[i]);
            setPermissions(listid, all[i], "edit");
        }
    }
}

// bad practice, listid is global for *now* while I
// straighten out everything else
function setPermissions(listid, user, permission) {
    $.ajax({
        url: "/api/setpermissions",
        method: "POST",
        data: {
            listid: listid,
            target: user,
            permission: permission
        },
        success: function(data, status, jqxhr) {
            getCurrentPerms(listid);
        },
        error: function(jqxhr, error, exception) {
            getCurrentPerms(listid);
            console.log(error);
            $("#link").html("Oops, that user doesn't exist!");
            $("#link").fadeIn(500)
            setTimeout(hideLink, 3000);
        }
    });
}

function hideLink() {
    $("#link").fadeOut();
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
            if (perm === 'own') {
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
            /*else {
                if (confirm("Are you sure you want to permanently remove yourself from this list?")) {
                    $.ajax({
                        url: "/api/mylists/remove",
                        method: 'POST',
                        data: {
                            listid: listid,
                        },
                        success: function(data, status, jqxhr) {
                            alert("You have removed list " + listid);
                            location.reload(true); // reload from server not cache
                        }
                    });
                }
            }*/
        }
    });
}