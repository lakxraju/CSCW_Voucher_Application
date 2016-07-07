/**
 * @author SharathChandra
 created on  01/07/2016
 */

var app = angular.module('app', ["ui.bootstrap", "ngAnimate", "ngRoute", "ngCookies", "blockUI", "smart-table"]);

/**
 * Configure the Routes
 */
//var IPAddress = "10.144.103.72:5000"
var IPAddress = "192.168.0.29:5000"
app.config(['$routeProvider', function ($routeProvider) {
    $routeProvider

        .when("/", {templateUrl: "partials/login.html", controller: "LoginCtrl"})
        .when("/register", {templateUrl: "partials/registration.html", controller: "RegCtrl"})
        .when("/main", {templateUrl: "partials/main.html", controller: "voucherCtrl"})

}]);


app.controller('LoginCtrl', function ($scope, $http, $location, $cookies) {

    $scope.username = "";
    $scope.password = "";

    $scope.submit = function () {
        if ($scope.username && $scope.password) {
            var user = $scope.username;
            var pass = $scope.password;

            $http({
                method: 'POST',
                url: 'http://' + IPAddress + '/voucherApp/signIn',
                headers: {'Content-Type': 'application/json'},
                data: {
                    username: user,
                    password: pass
                }
            }).success(function (data) {

                console.log(data);

                $cookies.put("privkey", data.privateKey);
                console.log(data.privateKey + "-----1------2---3----")
                $cookies.put("user", user);


                $cookies.put("pubkey", data.publicKey);
                var value = $cookies.get("privkey");

                console.log(value);

                $location.path('/main');

            });
        }

        else {
            alert("Invalid Login");
        }
    };
});


app.controller('RegCtrl', function ($scope, $location, $http, $cookies) {

    $scope.username = "";
    $scope.password = "";
    $scope.type = "";

    $scope.register = function () {

        // use $.param jQuery function to serialize data from JSON
        if ($scope.username && $scope.password && $scope.type) {

            $http({
                method: 'POST',
                url: 'http://' + IPAddress + '/voucherApp/createUser',
                headers: {'Content-Type': 'application/json'},
                data: {
                    username: $scope.username,
                    password: $scope.password,
                    type: $scope.type
                }
            }).success(function (data) {

                console.log(data);

                alert("Registration successful! Login with your credentials now.")
                $location.path('/');


            });

        }
        else {
            alert("Enter all the fields");
        }
    };

});


app.controller('voucherCtrl', function ($scope, $filter, $http, $uibModal, $cookies, $timeout, blockUI,$window) {


    $scope.nameOfVoucher = "";
    $scope.valueOfVoucher = "";

    //$http.get('data/sample.json')
    //    .success(function (data) {
    //        $scope.items = data;
    //        console.log($scope.items);
    //        console.log("after this");
    //
    //
    //        if ($scope.items.usertype == 1) {
    //
    //            $scope.items.usertype = "Donor"
    //        }
    //        else if ($scope.items.usertype == 2) {
    //            $scope.items.usertype = "Customer"
    //        }
    //        else if ($scope.items.usertype == 3) {
    //            $scope.items.usertype = "Company"
    //        }
    //
    //    });

    $scope.selectedItem = [];

    $scope.selItem = function (myItem) {

        $scope.selectedItem = myItem
        console.log(myItem);
    }

    $http({
        method: 'GET',
        url: 'http://' + IPAddress + '/voucherApp/getOwnedIDs?username=' + $cookies.get("user")
    }).then(function successCallback(response) {
        $scope.items = response.data
        console.log($scope.items)
        console.log("--------")

        if ($scope.items.usertype == 1) {

            $scope.items.usertype = "Donor"
        }
        else if ($scope.items.usertype == 2) {
            $scope.items.usertype = "Customer"
        }
        else if ($scope.items.usertype == 3) {
            $scope.items.usertype = "Company"
        }


    }, function errorCallback(response) {
        // called asynchronously if an error occurs
        // or server returns response with an error status.
    });



     $http({
        method: 'GET',
        url: 'http://' + IPAddress + '/voucherApp/getHistory?username=' + $cookies.get("user")
    }).then(function successCallback(response) {
        $scope.history = response.data

         console.log($scope.history);

    }, function errorCallback(response) {
        // called asynchronously if an error occurs
        // or server returns response with an error status.
    });




    $scope.animationsEnabled = true;

    $scope.toggleAnimation = function () {
        $scope.animationsEnabled = !$scope.animationsEnabled;
    };

    $scope.transferVoucher = function (transferData) {

        if ((Object.keys(transferData).length) == 0) {


            alert("Please choose a voucher to transfer")

        }


        else {


            if ($scope.items.usertype == 'Donor') {

                $scope.open('sm', transferData.txid, transferData.cid)
                console.log($scope.items.usertype)

            }

            else if ($scope.items.usertype == 'Company') {

                $scope.open('sm', transferData.txid, transferData.cid)
                console.log($scope.items.usertype)
            }

            else if ($scope.items.usertype == 'Customer') {
                console.log($scope.items.usertype)
                blockUI.start("Transferring voucher...");

                $timeout(function () {
                    blockUI.message('Adding transaction to Bigchain ...');
                }, 2000);


                $timeout(function () {
                    blockUI.stop();
                }, 1000);

                console.log(transferData);
                console.log("---HAHA--")

                var trans_to = transferData.name;
                var private_key = $cookies.get("privkey");
                var trans_from = $scope.items.username;
                var aid = transferData.txid;
                var cid = transferData.cid;

                console.log(trans_to);
                console.log(trans_from);
                console.log(private_key);
                console.log(aid);


                $http({
                    method: 'POST',
                    url: 'http://' + IPAddress + '/voucherApp/transferVoucher',
                    headers: {'Content-Type': 'application/json'},
                    data: {
                        target_username: trans_to,
                        source_username: trans_from,
                        private_key: $cookies.get("privkey"),
                        asset_id: aid,
                        cid: cid
                    }
                }).success(function (data) {

                    console.log(data);
                    $window.location.reload();

                });


            }

        }

    };


    $scope.open = function (size, aid, cid) {


        console.log("inside open function")

        $scope.aid = aid;
        $scope.cid = cid;

        console.log($scope.aid + "AID this is")
        console.log($scope.cid + "CID this is")

        console.log($scope.items);


        var modalInstance = $uibModal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'myModalContent.html',
            controller: 'ModalInstanceCtrl',
            size: size,
            resolve: {
                items: function () {
                    return {'data': $scope.items, 'assetid': $scope.aid, 'cid': $scope.cid}
                }
            }

        });

    };


    $scope.newVoucher = function (size) {


        var modalInstance = $uibModal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'myModalContent2.html',
            controller: 'ModalInstanceCtrl2',
            size: size,
            resolve: {
                items: function () {
                    return {'data': $scope.items}
                }
            }

        });

    };


});

app.controller('ModalInstanceCtrl2', function ($scope, $http, $uibModalInstance, items, $cookies, $window) {
    $scope.items = items.data;

    console.log(items);

    $scope.ok = function () {

        var trans_from = $cookies.get("user");
        var vname = $scope.nameOfVoucher;
        var vvalue = $scope.valueOfVoucher;


        console.log(trans_from);
        console.log(vname);
        console.log(vvalue);


        $http({
            method: 'POST',
            url: 'http://' + IPAddress + '/voucherApp/createVoucher',
            headers: {'Content-Type': 'application/json'},
            data: {
                username: trans_from,
                voucher_name: vname,
                value: vvalue
            }
        }).success(function (data) {

            console.log(data);

            $uibModalInstance.close();
            if(data.status == "error")
                alert(data.errorMessage);
            else
                $window.location.reload();

        });

    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});


app.controller('ModalInstanceCtrl', function ($scope, $http, $uibModalInstance, items, $cookies, $window, blockUI,$timeout) {
    $scope.items = items.data;
    $scope.aid = items.assetid;
    $scope.cid = items.cid;


    $scope.ok = function () {


        blockUI.start("Transferring voucher...");

        $timeout(function () {
            blockUI.message('Adding transaction to Bigchain ...');
        }, 2000);


        $timeout(function () {
            blockUI.stop();
        }, 1000);


        console.log($scope.items);
        console.log("------")
        console.log($scope.aid + "in 11111");
        console.log($scope.cid + "in 11111");


        var trans_to = $scope.transfer_to;
        var private_key = $cookies.get("privkey");
        var trans_from = $scope.items.username;
        var aid = $scope.aid;
        var cid = $scope.cid;

        console.log(trans_to);
        console.log(trans_from);
        console.log(private_key);
        console.log(aid);


        $http({
            method: 'POST',
            url: 'http://' + IPAddress + '/voucherApp/transferVoucher',
            headers: {'Content-Type': 'application/json'},
            data: {
                target_username: trans_to,
                source_username: trans_from,
                private_key: $cookies.get("privkey"),
                asset_id: aid,
                cid: cid
            }
        }).success(function (data) {

            console.log(data);

            $uibModalInstance.close();
            $window.location.reload();

        });

    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});
