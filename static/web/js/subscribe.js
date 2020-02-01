document.addEventListener("DOMContentLoaded", () => {
    if (!('CBot' in window)) {
        return;
    }
    var stripe = Stripe(CBot.SPK);
    var checkoutSessionId = CBot.SCid;

    // Initiate payment
    stripe
        .redirectToCheckout({
            sessionId: checkoutSessionId,
            billingAddressCollection: 'auto',
    })
    .then(function(result) {
        console.log("error");
        // If `redirectToCheckout` fails due to a browser or network
        // error, display the localized error message to your customer
        // using `result.error.message`.
    })
    .catch(function(err) {
        console.log(err);
    });
});