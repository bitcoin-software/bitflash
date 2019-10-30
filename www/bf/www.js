var btcusd = 0
var ltcbtc = 0
var ltcmax = 0
var cur = "N/A"
var charge_id = "N/A"
var invoice_completed = false

$("#destination-address").on('input', function(){
  var str=$("#destination-address").val()
  //alert(str.startsWith("1"))
  if ( str.startsWith("1") || str.startsWith("bc1") || str.startsWith("3") )
  {
    var amount=$("#amount-field").val()
    cur = "BTC"
    $('#address-currency').text('#BTC');
    $('#amount').text('Amount (0.01 BTC max)');
    if (isNaN(amount) == true) {
        $("#txbutton").attr("disabled", false);
    }
  } else if ( str.startsWith("L") || str.startsWith("ltc1") )
  {
    var amount=$("#amount-field").val()
    cur = "LTC"
    $('#address-currency').text('#LTC');
    $('#amount').text('Amount (' + ltcmax + ' LTC max)');
    if (isNaN(amount) == true) {
        $("#txbutton").attr("disabled", false);
    }
  } else if ( str.startsWith("bitcoin:?r=https://bitpay.com/i/") ) {
     $.ajax({

               url: "https://api.bitflash.club/bitpay",
               type: "POST",
                data: {'url': str.replace("bitcoin:?r=", "")}
                }).then(function(data) {
                    $("#destination-address").val(data.address)
                    $("#amount-field").val(data.amount)
                    $("#txbutton").attr("disabled", false);
                })
  } else {
    var amount=$("#amount-field").val()
    $('#address-currency').text('Wrong address!');
    $("#txbutton").attr("disabled", !isNaN(amount));

  }

});

$("#amount-field").on('input', function(){
  var amount=$("#amount-field").val()

  if (isNaN(amount)) {
    $("#txbutton").attr("disabled", true);
    $("#amount-field").val("");
    $("#amount-field").attr("placeholder", "Must be a number!");
  } else if ((amount > 0) && (amount <= 0.01) && (cur === "BTC")) {
    $("#txbutton").attr("disabled", false);
  } else if ((amount > 0) && (amount < ltcmax) && (cur === "LTC")) {
    $("#txbutton").attr("disabled", false);
  }
});

$(document).ready(function(){
    $("#txbutton").attr("disabled", true);

    $.ajax({
        url: "https://api.bitflash.club/getrates"
    }).then(function(data) {
        ltcbtc=data.ltcbtc
        btcusd=data.btcusd
        ltcmax = parseFloat(0.01 / ltcbtc).toFixed(5);
    });

    $.ajax({
        url: "https://api.bitflash.club/getstatus"
    }).then(function(data) {
        btc_percent=data.btc
        ltc_percent=data.ltc
        $("#btc-status").text(btc_percent);
        $("#ltc-status").text(ltc_percent);

    });

    //$.ajax({
    //    url: "https://api.bitflash.club/donate"
    //}).then(function(data) {
    //    $('#qrlink').attr("href", "lightning:"+data.bolt);
    //    new QRCode(document.getElementById("qrcode"), data.bolt);
    //});

});

function getdata() {
    var amount=$("#amount-field").val()
    if (amount <= 0) {
        $("#amount-field").val("");
        $("#amount-field").attr("placeholder", "Wrong amount!");
        $("#txbutton").attr("disabled", true);
    } else {
        $("#txbutton").attr("disabled", true);
        $("#txbutton").text("Processing...");
        $("#order").hide()
        $("#payment").show()
        $.ajax({
            url: "https://api.bitflash.club/new",
            type: "POST",
            data: {'address': $("#destination-address").val(), 'amount': amount}
        }).then(function(data) {
           $("#payment").hide()
           $("#payment-data").show()
           $('#qrlink-payment').attr("href", "lightning:"+data.invoices.bolt11);
           new QRCode(document.getElementById("qr"), data.invoices.bolt11);
           $('#bolt11-text').text(data.bolt11);
           $('#order-id').html("<b>Order ID:</b> " + data.invoices);
           $('#order-payto').html("Pay network fee of " + data.invoices[0].network_fee_sat + " <i>satoshi</i> and BitFlash fee of " + data.invoices.fee_satoshi + " <i>satoshi</i>, total: " + data.tobe_paid_satoshi + "  <i>satoshi</i> (" + parseFloat(data.tobe_paid_satoshi/100000000*btcusd).toFixed(2) + " USD or " + parseFloat(data.tobe_paid_satoshi/100000000).toFixed(5) + " BTC)")
           $('#order-receiveto').html("We will send <b>" + data.invoices.receiver_amount + " " + data.invoices.receiver_currency + "</b> to <a href=\"https://chain.so/resolver?query=" + data.receiver + "\">" + data.receiver + "</a> after LN invoice is paid");
           charge_id = data.charge_id
           setInterval(function() {
            //your jQuery ajax code
                $.ajax({
               url: "https://api.bitflash.club/invoiceinfo",
               type: "POST",
                data: {'id': charge_id}
                }).then(function(data) {
                    if (data.status === 'paid' && !invoice_completed) {
                        invoice_completed = true
                        $("#qr").html('<img src="./bf/paid.png">')
                        $('#bolt11-text').text("Thank you! We will make transaction ASAP!");
                        $('#qr-title').text("PAID!");
                    } else if (data.status === 'expired' && !invoice_completed) {
                        invoice_completed = true
                        $("#qr").html('<img src="./bf/expired.png">')
                        $('#bolt11-text').text("Your order EXPIRED!");
                        $('#qr-title').text("EXPIRED!");
                    }
                })

            }, 1000 * 5 ); //each 5 seconds test invoice data

        });
    }
}

function startnew() {
  window.location.replace("./");
 }