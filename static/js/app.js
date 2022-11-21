$(function () {
    $('#opt_institution').prop('disabled', 'disabled');

    $('#list').DataTable( {
        scrollY: 400,
        scroller: true,
        dom: 'Bfrtip',
        buttons: [
            //'copy', 'csv', 'excel', 'pdf', 'print'
            'csv', 'excel', 'pdf'
        ]
    });
})
let items = [];
var message;
var dynamicErrorMsg = function () { return message; }

function onAdditems(id ,description, qty, unitsInStock, unitPrice, depositRate, forRent, forPurchase, forCutting) {
    var item = {'id' : id, 
            'item' : description, 
            'status' : 'open',
            'orderKind' : '', 
            'addedToCart': true, 
            'qty': parseInt(qty),
            'unitsInStock': parseInt(unitsInStock),
            'unitPrice': parseFloat(unitPrice),
            'depositRate': parseFloat(depositRate),
            'forRent': parseInt(forRent),
            'forPurchase':parseInt(forPurchase),
            'forCutting': parseInt(forCutting)
        };

    var _orderKinds = $("input[name='orderKind']");
    for(var i =0; i < _orderKinds.length; i++){
        var orderKind = _orderKinds[i];
        if(orderKind.id.replace('_orderKind','') == id){
            if($(orderKind).prop('checked'))
                item.orderKind = $(orderKind).val();
        }
    }

    if ($('#' + id + '_orderKind').val() == undefined){
        if (item.forRent == 1)
            item.orderKind = 'rent';
        if (item.forPurchase == 1)
            item.orderKind = 'buy';
        if (item.forCutting == 1)
            item.orderKind = 'cutitng';        
    }

    if(!item.orderKind){
        var elm ="<div class='error'>* Please choose one.</div>"
        $(elm).appendTo("#"+ id);
        return false;
    }
    else
    {
        $("div .error").remove()
    }

    var _orderKinds = $("input[name='orderKind']");
    for(var i =0; i < _orderKinds.length; i++){
        var orderKind = _orderKinds[i];
        if(orderKind.id.replace('_orderKind','') == id){
            if($(orderKind).prop('checked'))
                $(orderKind).prop('checked','');
        }
    }
      
    if (qty > 0) {
        item.qty = parseInt(qty);    
        items.push(item);
        localStorage.setItem('items', JSON.stringify(items));

        var btnAdd = $('#btn_' + id + '_add');
        var btnRemove = $('#btn_' + id + '_remove');
        $(btnAdd).prop('disabled', 'disabled');
        $(btnRemove).prop('disabled', '');
        $('#'+ id +'_quantity').css('border',"1px solid #ced4da");
    }else{
        $('#'+ id +'_quantity').css('border',"1px solid red");
    }
   return false;
}

function onRemoveitems(id, description, qty) {
    items = JSON.parse(localStorage.getItem('items'));
    var _items = items.filter((item, index) => item.id != id);;
    items = _items;
    localStorage.setItem('items', JSON.stringify(items));

    var btnAdd = $('#btn_' + id + '_add');
    var btnRemove = $('#btn_' + id + '_remove');
    $(btnRemove).prop('disabled', 'disabled');
    $(btnAdd).prop('disabled', '');


    var desc = $(description).val();
    var _qty = $(qty).val();

    if (desc)
        $(description).val('')

    if (_qty)
        $(qty).val(0)

    return false;
}

function updateOrderHandler(element, id, location){
    var status = $('#'+element).val();
    var url = `/${location}/order/${id}/update/${status}`;
    $.post(url, null, function (data, status) {
        try {
          if (status == 'success') {
            location.reload();
          }
        } catch (e) {
            return false;
        }
    })
}

function calalogRowEdit(id)
{
    var url = `/catalogs/${id}`;
    location.replace(url);
    return false;
}

function onDeleteCatalog(id){
    var url = `/catalog/${id}/delete`;
    $.post(url, null, function (data, status) {
        try {
          if (status == 'success') 
          {
            localStorage.clear();
            var resp =JSON.parse(data);
            location.replace(resp.redirect_url);
          }
        } catch (e) {
            return false;
        }
      })
}

function qtyOnchanged(qty ,unitInStock){
    var inStock = parseInt(unitInStock);
    var _qty = parseInt($(qty).val());

    if (_qty > inStock)
        $(qty).val(inStock);

    return false;    
}

$('#institution').on('change', function () {
    var option = $(this).val();
    if (option == 'other')
        $('#opt_institution').prop('disabled', '');
    else
        $('#opt_institution').prop('disabled', 'disabled');
});

$("input[name='shipMethod']").on('change', function () {
    var option = $(this).val();

    if ($(this).prop('checked') && option == 'Postage')
        $('#address').prop('disabled', '');
    else
        $('#address').prop('disabled', 'disabled');
})

$('#btnSubmit').on('click', function () {
    $('#orderForm').validate({
        rules: {
            firstName: { firstNameIsRequired: '' },
            lastName: { lastNameIsRequired: '' },
            opt_institution: { institutionIsRequired: '' },
            major: { majorIsRequired: '' },
            weight: { weightIsRequired: '' },
            height: { heightIsRequired: '' },
            mobileNo: { mobileNoIsRequired: '' },
            lineId: { lineIdIsRequired: '' },
            color: { colorIsRequired: '' },
            orderLocate: { orderLocateIsRequired: '' },
            myitems: { itemsCannotBeEmpty: '' },
            shipMethod: { shipMethodIsRequired: '' },
            address: { addressCannotBeEmpty: '' }
        },
        messages: {

        },
        errorPlacement: function (error, element) {
            if (element.attr("name") == "orderLocate")
                error.insertAfter("#errors");
            else if (element.attr("name") == "shipMethod")
                error.insertAfter("#shipMethods_errors");
            else if (element.attr("name") == "myitems")
                error.insertBefore(element);
            else
                error.insertAfter(element);
        },
        submitHandler: function (form) {
            formSubmit_handler(form);
            return false;
        }
    })
});

$('#catalogSubmit').on('click', function(){
    $('#catalogForm').validate({
        rules: {
            catalogName: { catalogNameIsRequired: '' },
            unitsInstock: { unitsInStockIsRequired: '' },
            unitPrice: { unitPriceIsRequired: '' },
            depositRate: { depositRateRequired: '' }
        },
        messages: {

        },
        errorPlacement: function (error, element) {
            error.insertAfter(element);
        },
        submitHandler: function (form) {
            form.submit();
            return false;
        }
    })
});

function formSubmit_handler(form) {
    var url = form.action;
    var formData = JSON.stringify($('#' + form.id).serializeArray());
    formData = JSON.parse(formData);
    formData.push({ 'name': 'orderItems', 'value': localStorage.getItem('items') });

    $.post(url, formData, function (data, status) {
      try {
        if (status == 'success') 
        {
          localStorage.clear();
          var resp =JSON.parse(data);
          location.replace(resp.redirect_url);
        }
      } catch (e) {
          return false;
      }
    })
}

$.validator.addMethod("catalogNameIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply catalog name.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("unitsInStockIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply units in stock.';
        return false;
    }

    if (parseInt(value) == 0) {
        message = '* Units in stock must be greater than 0.';
        return false;
    }

    return value.length > 0 && parseInt(value) > 0;
}, dynamicErrorMsg);

$.validator.addMethod("unitPriceIsRequired", function (value, element) {
    message ='';
    if (value.length == 0 || !value) {
        message = '* Please supply unit price.';
        return false;
    }

    if (parseFloat(value) == 0.0 || parseFloat(value) == 0) {
        message = '* Unit price must be greater than 0.';
        return false;
    }

    return value.length > 0 && parseFloat(value) > 0;
}, dynamicErrorMsg);

$.validator.addMethod("depositRateRequired", function (value, element) {
    message ='';
    var rentOnly = $('#forRentOnly').prop('checked');
    var cuttingOnly = $('#forCuttingOnly').prop('checked');

    if ((rentOnly || cuttingOnly) && (value.length == 0 || !value)) {
        message = '* Please supply deposit rate.';
        return false;
    }

    if ((rentOnly || cuttingOnly) && (parseFloat(value) == 0.0 || parseFloat(value) == 0)) {
        message = '* Deposit rate must be greater than 0.';
        return false;
    }

    return (!(rentOnly || cuttingOnly) || parseFloat(value) > 0);
}, dynamicErrorMsg);

$.validator.addMethod("firstNameIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply first name.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("lastNameIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply last name.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("institutionIsRequired", function (value, element) {
    var institution = $('#institution').val();

    if (institution == 'other' && value.length == 0 || !value) {
        message = '* Please supply institution.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("majorIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply major.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("weightIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply weight.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("heightIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply height.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("mobileNoIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply mobile phone.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("lineIdIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply line id.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("colorIsRequired", function (value, element) {
    if (value.length == 0 || !value) {
        message = '* Please supply color.';
        return false;
    }
    return value.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("orderLocateIsRequired", function (value, element) {
    var options = $("input[name='orderLocate']");
    var isSelected = false;
    for (var i = 0; i < options.length; i++) {
        var option = options[i];
        if ($(option).prop('checked')) {
            isSelected = true;
            break;
        }
    }
    if (!isSelected) {
        message = '* Please select your order location.';
        return false;
    }
    return isSelected;
}, dynamicErrorMsg);

$.validator.addMethod("shipMethodIsRequired", function (value, element) {
    var options = $("input[name='shipMethod']");
    var isSelected = false;
    for (var i = 0; i < options.length; i++) {
        var option = options[i];
        if ($(option).prop('checked')) {
            isSelected = true;
            break;
        }
    }
    if (!isSelected) {
        message = '* Please select shipping methods.';
        return false;
    }
    return isSelected;
}, dynamicErrorMsg);

$.validator.addMethod("itemsCannotBeEmpty", function (value, element) {
    var lineItems = JSON.parse(localStorage.getItem('items'));
    if (lineItems == null || lineItems.length == 0) {
        message = "* Please add 1 or more item(s)"
        return false;
    }
    return lineItems != null || lineItems.length > 0;
}, dynamicErrorMsg);

$.validator.addMethod("addressCannotBeEmpty", function (value, element) {
    var option = $("#Postage").prop('checked');
    var address = $('#address').val();
    if (option && address.trim().length == 0) {
        message = '* Please supply shipping address.';
        return false;
    }
    return option && address.trim().length > 0;
}, dynamicErrorMsg);
