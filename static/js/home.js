$(document).ready(function()
{
    // upon clicking the last list item (with a plus sign), a new
    // list item will automatically be added to the bottom of the list
    $(".list").on("click", ".lastListItem", function()
    {
        $(".lastListItem").before("<div class='listItem'> <!--list item--> <div class='itemTitle'> <input type='text' placeholder='Item'> </div> <img src='/static/img/down.svg'> <div class='attributes'> <!--all item attributes--> <div class='attribute'> <!--single item attribute--> <div class='key' ><input type='text' placeholder='Attribute' ></div ><div class='value' ><input type='text' placeholder='Value' ></div> </div> <div class='lastAttribute'> <input type='text' value=' +' disabled> </div> </div> </div>");
    });

    // upon clicking the "V" shaped icon, the list of attributes
    // will slide down and appear
    $(".list").on("click", "img", function()
    {
        $(this).find("attribute").slideDown(500);
        $(this).find("attribute").attr("display","block");
    });

    // upon the "title" li's losing focus, the list of attributes
    // will slide back up and hide
    $(".list").on("blur", "listItem", function()
    {
        $(this).find("attribute").slideUp(500);
    });
});