$(document).ready(function()
{

    // creates list on first serious attempt at making a list
    $(".list").one("focusout", ifNoListMakeOne);

    $(".list").on('focusout', ".key input", function(){
        var newkey = $(this).val();

        var listitem = $(this).parents().eq(4-1);
        var kvps = $(this).parents().eq(3-1);
        var this_kvp = $(this).parents().eq(2-1);
        
        var ind = kvps.children().index(this_kvp);
        var entryind = $(".list .listItem").index(listitem);
        
        $.ajax({
            url: "/ajax/savekey",
            method: 'POST',
            data: {
                listid: listid,
                index: ind,
                entryind: entryind,
                newvalue: newkey
            },
            success: function(data, status, jqxhr){
                console.log("key " + newkey + " saved to position " + ind) // debug
            }
        })
    });

    $(".list").on('focusout', ".value input", function(){
        var newval = $(this).val();

        var listitem = $(this).parents().eq(4-1);
        var kvps = $(this).parents().eq(3-1);
        var this_kvp = $(this).parents().eq(2-1);
        
        var ind = kvps.children().index(this_kvp);
        var entryind = $(".list .listItem").index(listitem);
        
        $.ajax({
            url: "/ajax/savevalue",
            method: 'POST',
            data: {
                listid: listid,
                index: ind,
                entryind: entryind,
                newvalue: newval
            },
            success: function(data, status, jqxhr){
                console.log("value " + newval + " saved to position " + ind) // debug
            }
        })
    });
    
    // upon clicking the last list item (with a plus sign), a new
    // list item will automatically be added to the bottom of the list
    $(".list").on("click", ".lastListItem", addItem);
    
    // upon clicking the last item attribute, a new item
    // attribute entry will be automatically added to the bottom
    // of the list
    $(".list").on("click", ".lastAttribute", addAttribute);
    
    // testing Ajax connection for now
	/*$(".list").on("focusout",function(){
        $("#catalist").ajaxSubmit();
	});*/

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

function ifNoListMakeOne(){
    if(listid===null){
        $.ajax({
            url: "/ajax/makelist",
            method: 'GET',
            data: {
                title: $(".listtitle input").val()
            },
            success: function(data, status, jqxhr){
                // get list id, which we want to be a global var
                listid = data.id;
                // put the url in later >.<
                $("#link").html('Access or share your list at: <br><a href="http://0.0.0.0:6005/list/' + listid + '">http://0.0.0.0:6005/list/' + listid + "</a>");
                console.log('http://0.0.0.0:6005/list/' + listid);
            }
        });
    }
}

function addItem()
{
    $(".lastListItem").before("<div class='listItem'> <!--list item--> <div class='itemTitle'> <input type='text' placeholder='Item'> </div> <img src='/static/img/down.svg'> <div class='attributes'> <!--all item attributes--> <div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Key' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='minus'></div> </div> <div class='lastAttribute'> <input type='text' value=' +' disabled> </div> </div> </div>");
}

function addAttribute()
{
    $(this).before("<div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Key' ></div ><div class='value' ><input type='text' placeholder='Value' ></div><div class='minus'></div></div>");
}

function deleteItem(){
    // do ajax-y things
}

function deleteAttribute(){
    // do more ajax-y things
}