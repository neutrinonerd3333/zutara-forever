/* listid initialized to null, will get assigned the listid of the list
 * when we create it in the database
 */
var listid = null;
var pathname = window.location.pathname;
var n = pathname.search(/^\/list\/.+/, pathname);
if (n === 0) {
    listid = pathname.slice(6);
}

$(document).ready(function()
{
    //$(".list").one("mouseenter", welcome);
    
    // creates list on first serious attempt at making a list
    // $(".list").one("focusout", ifNoListMakeOne);
    $(".list").on('focusout', ".key input", function(){
        var that = $(this);
        ifNoListMakeOne(function(){saveKeyOrValue(that, "key");});
    });

    $(".list").on('focusout', ".value input", function(){
        var that = $(this);
        ifNoListMakeOne(function(){saveKeyOrValue(that, "value");});
    });

    $(".list").on('focusin', ".itemTitle input", function(){
        var icon = $(this).parent().next();
        var heart = $(this).parent().prev();
        $(heart).css("background-position","-6em -3em");
        if(isArrowUp(icon)){
            $(icon).css("background-position","-1.5em -3em");
        }
        else {
            $(icon).css("background-position","0 -3em");
        }
        
    });
    $(".list").on('focusout', ".itemTitle input", function(){
        var icon = $(this).parent().next();
        var heart = $(this).parent().prev();
        $(heart).css("background-position","-6em 0");
        if(isArrowUp(icon)){
            $(icon).css("background-position","-1.5em 0");
        }
        else {
            $(icon).css("background-position","0 0");
        }
        
        var that = $(this);
        ifNoListMakeOne(function(){
            var newval = that.val();
            var grandpa = that.parents().eq(2-1);
            var entryind = $(".list .listItem").index(grandpa);

            $.ajax({
                url: "/api/saveentrytitle",
                method: 'POST',
                data: {
                    listid: listid,
                    entryind: entryind,
                    newvalue: newval
                },
                success: function(data, status, jqxhr){
                    // console.log("entry title " + newval + " saved to entry " + entryind);
                }
            });
        });
    });

    // no need to do "on" because we won't have multiple listTitle's
    $(".listTitle input").focusout(function(){
        var that = $(this);
        ifNoListMakeOne(function(){
            var newval = that.val();
            $.ajax({
                url: "/api/savelisttitle",
                method: 'POST',
                data: {
                    listid: listid,
                    newvalue: newval
                },
                success: function(data, status, jqxhr){
                    // console.log("list title " + newval + " saved to list " + listid);
                }
            });
        });
    });


    /* DOM Manipulation
     * add items
     */
    
    // upon clicking the last list item (with a plus sign), a new
    // list item will automatically be added to the bottom of the list
    $(".list").on("click", ".lastListItem", addItem);
    
    // upon clicking the last item attribute, a new item
    // attribute entry will be automatically added to the bottom
    // of the list
    $(".list").on("click", ".lastAttribute", addAttribute);

    // clicking the down arrow will show attributes
    // clicking the up arrow will hide the attributes
    var arrowUp = false;
    
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
            resize();
        }  
    });
    // clicking heart will add a vote to the item (or remove it if existing)
    $(".list").on("click", ".icon-heart", addVote);
    
    // clicking minus will delete the current key-value pair
    $(".list").on("click", ".icon-minus", function(){
        var item = $(this).closest(".listItem");
        var eind = $(".list .listItem").index(item);
        var siblings = $(this).closest(".attributes").children(".attribute");
        var kvpind = siblings.index($(this).closest(".attribute"));

        // delete from database
        $.ajax({
            url: "/api/deletekvp",
            method: 'POST',
            data: {
                listid: listid,
                entryind: eind,
                index: kvpind
            },
            success: function(data, status, jqxhr){
                // console.log("deleted kvp at entry " + eind + " index " + kvpind);
            }
        });

        $(this).closest(".attribute").remove();
    });
    
    
});

function ifNoListMakeOne(callback){
    if(listid===null){
        $.ajax({
            url: "/api/makelist",
            method: 'GET',
            data: {
                title: $(".listtitle input").val()
            },
            success: function(data, status, jqxhr){
                // get list id, which we want to be a global var

                listid = data.listid;
                rel_url = "/list/" + listid
                url = "http://" + location.host + rel_url
                $("#link").html('Access or share your list at: <br><a href="'+url+'">'+url+"</a>");
                // use pushState with same args to change url while preserving
                // original in browser history; replaceState does same w/o preserving
                window.history.pushState("", "Catalist", rel_url)
                callback()
            }
        });
    } else {
        callback();
    }
}

function addItem(){
    $(".lastListItem").before("<div class='listItem'> <!--list item--> <div class='icon-heart icon'></div>  <div class='itemTitle'> <input type='text' placeholder='Item'> </div> <div class='icon-down icon'></div> <div class='attributes'> <!--all item attributes--> <div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Key' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='icon-minus icon'></div> </div> <div class='lastAttribute'> <input type='text' value=' +' disabled> </div> </div> </div>");
    resize();
}

function addAttribute(){
    $(this).before("<div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Key' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='icon-minus icon'></div></div>");
    resize();
}

function saveKeyOrValue(that, toSave){
    if (toSave !== "key" && toSave !== "value"){
        throw "ValueError: argument of saveKeyOrValue must be 'key' or 'value'";
    }

    var newval = that.val();

    /* this code is rather ugly -- maybe elegantize lol */
    var listitem = that.parents().eq(4-1);
    var kvps = that.parents().eq(3-1);
    var this_kvp = that.parents().eq(2-1);
    
    var ind = kvps.children().index(this_kvp);
    var entryind = $(".list .listItem").index(listitem);

    $.ajax({
        url: "/api/save" + toSave,
        method: 'POST',
        data: {
            listid: listid,
            index: ind,
            entryind: entryind,
            newvalue: newval
        },
        success: function(data, status, jqxhr){
            // console.log(toSave + " " + newval + " saved to position " + ind) // for debug
        }
    })
}

function addVote(){
    alert("You clicked the heart!");
        
        var item = $(this).closest(".listItem");
        var eind = $(".list .listItem").index(item);
        console.log(eind);
        $.ajax({
            url: "/api/vote",
            method: 'POST',
            data: {
                listid: listid,
                entryind: eind,
                vote: 1
            },
            success: function(data, status, jqxhr){
                $(this).css("background-position","-10.5em 0");
                console.log("Current score is " + data.score);
            }
        });
}

function deleteItem(){
    // do ajax-y things
}

function deleteAttribute(){
    // do more ajax-y things
}

function resize() {
    $("body").css({
        "height": "100%",
        "background-size":"100% 100%",
        "background": "linear-gradient(to bottom, #4BF 0%,#5CE 60%,#AEF 100%",
        "background": "-moz-linear-gradient(top, #4BF 0%, #5CE 60%, #AEF 100%)",
        "background": "-webkit-linear-gradient(top, #4BF 0%,#5CE 60%,#AEF 100%)",
    });
}

function welcome() {
    $("#link").hide();
    $("#link").html("Welcome! Would you like a tutorial?");
    $("#link").fadeIn(500);
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