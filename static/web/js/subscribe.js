document.addEventListener("DOMContentLoaded", () => {

    if (!('CBot' in window)) {
        return;
    }


    var hasSubscription = window.hasSubscription ? Number(window.hasSubscription) : 1;

    if (!Boolean(hasSubscription)) {
        var stripe = Stripe(CBot.SPK);
        var checkoutSessionId = CBot.SCid;
        setTimeout(function () {
            document.getElementById("help").classList.remove('hidden');
        }, 5000);

        // Initiate payment
        stripe
            .redirectToCheckout({
                sessionId: checkoutSessionId,
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
    }
});