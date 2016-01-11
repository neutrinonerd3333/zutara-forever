$(document).ready(function()
{
    // upon clicking the last list item (with a plus sign), a new
    // list item will automatically be added to the bottom of the list
    $(".list").on("click", ".lastListItem", function()
    {
        $(".lastListItem").before("<div class='listItem'> <!--list item--> <div class='itemTitle'> <input type='text' placeholder='Item'> </div> <img src='/static/img/down.svg'> <div class='attributes'> <!--all item attributes--> <div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Attribute' ></div ><div class='value' ><input type='text' placeholder='Value' ></div> </div> <div class='lastAttribute'> <input type='text' value=' +' disabled> </div> </div> </div>");
    });
    
    // upon clicking the last item attribute, a new item
    // attribute entry will be automatically added to the bottom
    // of the list
    $(".list").on("click", ".lastAttribute", function()
    {
        $(this).before("<div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Attribute' ></div ><div class='value' ><input type='text' placeholder='Value' ></div> </div>");
    });

	/*
	$(stuff).focusout(function(){
		// skeleton for ajax call
        $.ajax(stuff)
	});
	*/

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
            $(this).prev(".itemTitle").find("input").css("border-radius","10px");
        }
        // if currently down arrow, click should show attributes and switch
        // to up arrow
        else
        {
            $(this).next(".attributes").slideDown(500);
            $(this).attr("src","/static/img/up.svg");
            $(this).prev(".itemTitle").find("input").css("border-radius","10px 10px 0 0");
        }
        
    });

});