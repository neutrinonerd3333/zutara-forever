/* listid initialized to null, will get assigned the listid of the list
 * when we create it in the database
 */
var listid = null;
var pathname = window.location.pathname;
var n = pathname.search(/^\/list\/.+/, pathname);
if (n === 0) {
    listid = pathname.slice(6);
}

$(document).ready(function() {
    if (listid === null){
        $(".list").one("input", makeList);
    }

    $("body").on('click', "input[type='url']", function() {
        $(this).select();
        // no need to copy for now
        // document.execCommand("copy");
        // alert("Link copied to clipboard!");
    });

    var loggedIn = false;
    $.ajax({
        url: "/api/loggedin",
        method: 'POST',
        success: function(data, status, jqxhr) {
            // logged in if true, guest if false
            if (data.loggedin) {
                authenticated();
            } else {
                guest();
            }
        }
    });

    // save
    $(".list").on('focusin', ".itemTitle input", function() {
        var icon = $(this).parent().next();
        var heart = $(this).parent().prev();

        var curListItem = $(this).closest(".listItem");
        // this starts at 1 cuz div before it
        var itemInd = $(curListItem).index();
        var totalItems = $(this).closest(".list").find(".listItem").length;

        if (totalItems === itemInd) {
            addItem(curListItem);
        }
    });

    /* DOM Manipulation, add items */

    // upon clicking the last item attribute, a new item
    // attribute entry will be automatically added to the bottom
    // of the list    
    $(".list").on('focusin', ".attribute * input", function() {
        var curAttribute = $(this).closest(".attribute");
        // starts at 0 cuz nothing else in attributes
        var attrInd = $(curAttribute).index() + 1;
        var totalItems = $(this).closest(".listItem").find(".attribute").length;

        if (totalItems === attrInd) {
            addAttribute(curAttribute);
        }
    });

    // clicking the down arrow will show attributes
    // clicking the up arrow will hide the attributes

    $(".list").on("click", ".icon-down", function() {
        // if currently up arrow, click should hide attributes and switch
        // to up arrow
        if (isArrowUp($(this))) {
            var attrs = $(this).next(".attributes");
            var that = $(this);
            $(attrs).slideUp(500, function(){
                that.prev(".itemTitle").find("input").css("border-radius", "20px");
            });
            $(this).css("background-position", "0 0");

            $(this).mouseenter(function() {
                $(this).css("background-position-y", "-3em");
            });
            $(this).mouseleave(function() {
                $(this).css("background-position-y", "0");
            });


            var nums = $(this).closest(".listItem").find(".attribute").length;
            // if more than one entry, check if any are empty
            if (nums > 1) {
                // find attributes following arrow img
                var atts = $(attrs).find(".attribute");
                // find the input fields under the key and value divs
                var keys = $(attrs).find(".key :input");
                var vals = $(attrs).find(".value :input");

                for (var i = atts.length - 1; i >= 0; i--) {
                    // get values of each attribute
                    key = $(keys[i]).val();
                    value = $(vals[i]).val();
                    // check if whole row empty
                    if (key.length === 0 && value.length === 0) {
                        $(atts[i]).remove();
                    }
                }
                var newLength = $(attrs).find(".attribute").length;
                if (newLength === 0) {
                    appendAttribute(attrs);
                }
            }
        }
        // if currently down arrow, click should show attributes and switch
        // to up arrow
        else {
            $(this).next(".attributes").slideDown(500);
            $(this).css("background-position", "-1.5em 0");
            $(this).prev(".itemTitle").find("input").css("border-radius", "20px 20px 0 0");
            resize();
        }
    });
    // clicking heart will add a vote to the item (or remove it if existing)
    $(".list").on("click", ".icon-heart", vote);

    // clicking a specific item's trash will delete that item
    $(".list").on("click", ".icon-trash-2", deleteEntry);

    // clicking minus will delete the current key-value pair
    $(".list").on("click", ".icon-minus", function() {
        var item = $(this).closest(".listItem");

        var totalItems = $(this).closest(".listItem").find(".attribute").length;
        if (totalItems > 1) {
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
                success: function(data, status, jqxhr) {
                    // console.log("deleted kvp at entry " + eind + " index " + kvpind);
                }
            });

            $(this).closest(".attribute").remove();

            // if we have a new last, we want new rounded corners

        } else {
            $("#link").html("Oops! you can't delete the last entry!");
        }
    });
});

function deleteEntry() {
    var entry = $(this).parent();

    var totalItems = $(this).closest(".list").find(".listItem").length;
    if (totalItems > 1) {
        var eind = $(".list .listItem").index(entry);

        // delete from database
        $.ajax({
            url: "/api/deleteentry",
            method: 'POST',
            data: {
                listid: listid,
                entryind: eind,
            },
            success: function(data, status, jqxhr) {
                // console.log("deleted entry");
            }
        });
        $(entry).remove();
    } else {
        $("#link").html("Oops! you can't delete the last item!");
        $("#link").show();
    }
}

function votesVisible() {
    $(".votes").show();
    $(".listItem").css("width", "90%");
    
    $(".list").on('mouseenter', ".listItem", buttonsVisible);
    $(".list").on('mouseleave', ".listItem", buttonsHidden);
}

function buttonsVisible() {
    $(this).find(".icon-heart").show();
    $(this).find(".itemTitle input").css({
        "padding": "0 6em 0 1em",
        "width": "calc(100% - 7em)"
    });
    $(this).find(".icon-trash-2").show();
}

function buttonsHidden() {
    $(this).find(".icon-heart").hide();
    $(this).find(".itemTitle input").css({
        "padding": "0 2.5em 0 1em",
        "width": "calc(100% - 3.5em)"
    });
    $(this).find(".icon-trash-2").hide();
}

function authenticated() {
    loggedIn = true;
    if($("#newuser").length > 0) {
        askForTutorial();
    }
    
    if (listid !== null) {
        // if this is route /list/<listid>, bind listeners
        enableLiveSave();
        $(".listItem").each(function(index) {
            loadVotes($(this));
        });
        $("#link input").show();
    }
    votesVisible();
}

function guest() {
    loggedIn = false;
    if (listid === null) {
        askForTutorial();
        // $(".list").one("mouseenter", askForTutorial);
    } else {
        getPublicPermission(listid)
    }
    $(".list").on('mouseenter', ".listItem", buttonsVisible);
    $(".list").on('mouseleave', ".listItem", buttonsHidden);
}

function getPublicPermission(listid) {
    $.ajax({
        data: {
            listid: listid
        },
        url: "/api/getpubliclevel",
        method: "POST",
        success: function(data, status, jqxhr) {
            if(data==="edit") {
                enableLiveSave();
            }
            else if(data==="view") {
                $(".list").find("input").prop('disabled', true);
            }
            else { enableLiveSave(); } // idk??
            $("#link input").show();
        }
    });
}

function askToMakeList() {
    $("#link").html("<div class='yes'>Click to Save</div> or <div class='no'>Nah</div>");
}

// all event bindings will be attached upon saving the list
// so since list MUST exist, no need to call ifNoListMakeOne
function enableLiveSave() {

    // binding to save key and value
    $(".list").on('focusout', ".key input", function() {
        var that = $(this);
        saveKeyOrValue(that, "key");
    });
    $(".list").on('focusout', ".value input", function() {
        var that = $(this);
        saveKeyOrValue(that, "value");
    });

    // binding to save title
    $(".list").on('focusout', ".itemTitle input", function() {
        var that = $(this);
        var newval = that.val();
        var grandpa = that.parents().eq(2 - 1);
        var entryind = $(".list .listItem").index(grandpa);

        $.ajax({
            url: "/api/saveentrytitle",
            method: 'POST',
            data: {
                listid: listid,
                entryind: entryind,
                newvalue: newval
            },
            success: function(data, status, jqxhr) {
                // console.log("entry title " + newval + " saved to entry " + entryind);
            }
        });
    });

    // no need to do "on" because we won't have multiple listTitle's
    $(".listTitle input").focusout(function() {
        var that = $(this);
        var newval = that.val();
        if (newval.length === 0) {
            newval = "untitled list";
        }
        $.ajax({
            url: "/api/savelisttitle",
            method: 'POST',
            data: {
                listid: listid,
                newvalue: newval
            },
            success: function(data, status, jqxhr) {
                // console.log("list title " + newval + " saved to list " + listid);
            }
        });
    });
}

function noSave() {
    if (confirm("Are you sure you don't want to save this list?")) {
        $(".list").off("focusout");
        $("#link").html("If you change your mind, <div class='yes'>click here to save</div>.");
    }
}

function makeList() {
    $.ajax({
        url: "/api/makelist",
        method: 'GET',
        data: {
            title: $(".listTitle input").val()
        },
        success: function(data, status, jqxhr) {
            // get list id, which we want to be a global var

            listid = data.listid;
            rel_url = "/list/" + listid
            url = "http://" + location.host + rel_url
            $("#link").html("Access or share your list at: <br><input type='url' id='listurl' value=" + url + ">");
            $("#link input").show();
            // use pushState with same args to change url while preserving
            // original in browser history; replaceState does same w/o preserving
            window.history.pushState("", "Catalist", rel_url)
        }
    });
    enableLiveSave();
}

// figures out whether selected item is last one
function isLastItem() {
    var curListItem = $(this).closest(".listItem");
    var totalItems = $(this).closest(".list").find(".listItem").length;
    var itemInd = $(curListItem).index(); // this starts at 1
    return totalItems === itemInd;
}

function addItem(curListItem) {
    $(curListItem).after("<div class='listItem'><div class='icon-trash-2'></div> <div class='votes'><div><b>0</b>&#9829;</div></div> <!--list item--> <div class='icon-heart icon'></div>  <div class='itemTitle'> <input type='text' placeholder='Item'> </div> <div class='icon-down icon'></div> <div class='attributes'> <!--all item attributes--> <div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Note' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='icon-minus icon'></div> </div></div> </div>");
    if (loggedIn) {
        votesVisible();
    }
    resize();
}

function addAttribute(curAttribute) {
    $(curAttribute).css("border-radius", "0");
    $(curAttribute).after("<div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Note' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='icon-minus icon'></div></div>");
    // $(curAttribute).next().css("border-radius", "0 0 20px 20px");
    resize();
}

function appendAttribute(parentElement) {
    $(parentElement).append("<div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Note' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='icon-minus icon'></div></div>");
    resize();
}

function saveKeyOrValue(that, toSave) {
    if (toSave !== "key" && toSave !== "value") {
        throw "ValueError: argument of saveKeyOrValue must be 'key' or 'value'";
    }

    var newval = that.val();

    /* this code is rather ugly -- maybe elegantize lol */
    var listitem = that.parents().eq(4 - 1);
    var kvps = that.parents().eq(3 - 1);
    var this_kvp = that.parents().eq(2 - 1);

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
        success: function(data, status, jqxhr) {
            // console.log(toSave + " " + newval + " saved to position " + ind) // for debug
        }
    })
}

function vote() {
    var that = $(this);
    if (isHeartFilled(that)) {
        deleteVote(that);
    } else {
        addVote(that);
    }
}

function addVote(that) {
    var item = $(that).closest(".listItem");
    var eind = $(".list .listItem").index(item);
    
    if(listid !== null)
    {
        // change it live
        var voteBox = $(item).find(".votes div");
        var curVal = $(voteBox).text();
        
        curVal = parseInt(curVal.substring(0, curVal.length-1));
        curVal = curVal + 1;
        $(voteBox).html('<div><b>' + curVal + '</b>&#9829;</div>');
    }
    
    $.ajax({
        url: "/api/vote",
        method: 'POST',
        data: {
            listid: listid,
            entryind: eind,
            vote: 1
        },
        success: function(data, status, jqxhr) {
            $(that).css("background-position", "-10.5em 0");

            $(that).mouseenter(function() {
                $(that).css("background-position-y", "-3em");
            });
            $(that).mouseleave(function() {
                $(that).css("background-position-y", "0");
            });

            // console.log("Current score is " + data.score);
            return true;
        },
        error: function(jqxhr, error, exception) {
            $.ajax({
                url: "/api/loggedin",
                method: 'POST',
                success: function(data, status, jqxhr) {
                    // logged in if true, guest if false
                    if (data.loggedin) {
                        $("#link").html("Oops! <div class='yes'>Click here to save the current list</div> to vote.");
                    } else {
                        $("#link").html("Oops! <a href='/login'>Click here to login</a> to vote.");
                    }
                }
            });
            $("body").one('click', ".yes", makeList);
        }
    });

}

// undo vote
function deleteVote(that) {
    var item = $(that).closest(".listItem");
    var eind = $(".list .listItem").index(item);
    
    var voteBox = $(item).find(".votes div");
    var curVal = $(voteBox).text();

    curVal = parseInt(curVal.substring(0, curVal.length-1));
    curVal = curVal + -1;
    if(curVal < 0) { curVal = 0; }
    $(voteBox).html('<div><b>' + curVal + '</b>&#9829;</div>');
    
    $.ajax({
        url: "/api/vote",
        method: 'POST',
        data: {
            listid: listid,
            entryind: eind,
            vote: 0
        },
        success: function(data, status, jqxhr) {
            $(that).css("background-position", "-6em 0");
            // console.log("Current score is " + data.score);
            return true;
        },
        error: function(jqxhr, error, exception) {
            $.ajax({
                url: "/api/loggedin",
                method: 'POST',
                success: function(data, status, jqxhr) {
                    // logged in if true, guest if false
                    if (data.loggedin) {
                        $("#link").html("Oops! <div class='yes'>Click here to save the current list</div> to vote.");
                    } else {
                        $("#link").html("Oops! <a href='/login'>Click here to login</a> to vote.");
                    }
                }
            });
        }
    });
}

function getPermissions(listid) {
    $.ajax({
        data: {
            listid: listid,
        },
        url: "/api/getpermissions",
        method: 'POST',
        success: function(data, status, jqxhr) {
            // logged in if true, guest if false
            // console.log(data.permission);
        }
    });
}

function resize() {
    $("body").css({
        "height": "100%",
        "background-size": "100% 100%",
        /*"background": "linear-gradient(to bottom, #09F 0%, #4BF 40%,#AEF 100%",
        "background": "-moz-linear-gradient(top, #09F 0%, #4BF 40%, #AEF 100%)",
        "background": "-webkit-linear-gradient(top, #09F 0%,#4BF 40%,#AEF 100%)",*/
    });
}

// that is the whole .listItem
function loadVotes(that) {
    var voteBox = $(that).find(".votes");

    var item = $(voteBox).closest(".listItem");
    var eind = $(".list .listItem").index(item);
    $.ajax({
        url: "/api/vote",
        method: 'POST',
        data: {
            listid: listid,
            entryind: eind,
            vote: 100
        },
        success: function(data, status, jqxhr) {
            $(voteBox).html("<div><b>" + data.score + "</b>&#9829;</div>");
            // default is 0, so only change if 1
            if (parseInt(data.current_vote) === 1) {
                $(voteBox).next().css("background-position", "-10.5em 0");
            }
            return data.cur_score;
        }
    });
}

function isArrowUp(icon) {
    var css = $(icon).css("background-position");
    // browser renders em into px, so 0 means left most = down arrow
    if (css.charAt(0) === "0") {
        return false;
    } else {
        // bind hover color if arrow up (css doesn't work)
        return true;
    }
}

// a bit of position hackiness
// should typically be 10 and 18, so 15 seems safe
function isHeartFilled(heart) {
    var css = $(heart).css("background-position");

    if (parseInt(css.substring(0, 3)) < -15) {
        return true;
    } else {
        return false;
    }
}

function askForTutorial() {
    $("#welcome").slideDown(300);
    $("#pro").one("click", noTutorial);
    $("#newb").one("click", tutorial);
}

function noTutorial() {
    $("#welcome").html("No problem! Have fun creating! We'll auto-save your lists.");
    setTimeout(hideTutorial, 2000);
}

function hideTutorial() {
    $("#welcome").fadeOut();
}

function tutorial() {
    hideTutorial();
    setTimeout(tutorial_1, 300);
}

function tutorial_1() {
    $(".bubble").fadeIn();
    $(".list").one("input", ".listTitle", tutorial_2);
}

function tutorial_2() {
    $(".bubble").fadeOut();
    $(".bubble-2").fadeIn();
    $(".list").one("input", ".itemTitle", tutorial_3);
}

function tutorial_3() {
    $(".bubble-2").fadeOut();
    $(".bubble-3").fadeIn();
    $(".list").one("click", ".icon-down", tutorial_4);
}

function tutorial_4() {
    $(".bubble-3").fadeOut();
    $(".bubble-4").fadeIn();
    $(".list").one("input", ".attribute", tutorial_5);
}

function tutorial_5() {
    $(".bubble-4").fadeOut();
    $("#welcome").html("And that's it! Remember to log in to manage your lists and vote on items!");
    $("#welcome").fadeIn();
}