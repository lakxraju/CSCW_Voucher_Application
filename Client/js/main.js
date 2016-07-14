/**
 * @author SharathChandra
 created on  01/07/2016
 */

var app = angular.module('app', ["ui.bootstrap", "ngAnimate", "ngRoute", "ngCookies", "blockUI", "smart-table", "trNgGrid", "ngPrettyJson"]);

/**
 * Configure the Routes
 */
var IPAddress = ""

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
                url: IPAddress + '/voucherApp/signIn',
                headers: {'Content-Type': 'application/json'},
                data: {
                    username: user,
                    password: pass
                }
            }).success(function (data) {

                console.log(data);

                if (data.status == "error")
                    alert(data.errorMessage);


                else {
                    $cookies.put("privkey", data.privateKey);
                    console.log(data.privateKey + "-----1------2---3----")
                    $cookies.put("user", user);


                    $cookies.put("pubkey", data.publicKey);
                    var value = $cookies.get("privkey");

                    console.log(value);

                    $location.path('/main');
                }
            });
        }

        else {
            alert("Enter both username and password");
        }
    };


    $scope.clearData = function () {


        $cookies.remove("user");
        $cookies.remove("privkey");
        $cookies.remove("pubkey");

        $location.path('/');

    }
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
                url: IPAddress + '/voucherApp/createUser',
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


app.controller('voucherCtrl', function ($scope, $filter, $http, $uibModal, $cookies, $timeout, blockUI, $window) {


    $scope.nameOfVoucher = "";
    $scope.valueOfVoucher = "";
    $scope.blockDetails = [];

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
        url: IPAddress + '/voucherApp/getOwnedIDs?username=' + $cookies.get("user")
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
        url: IPAddress + '/voucherApp/getHistory?username=' + $cookies.get("user")
    }).then(function successCallback(response) {

        $scope.historyList = response.data

        console.log($scope.historyList);


    }, function errorCallback(response) {
        // called asynchronously if an error occurs
        // or server returns response with an error status.
    });


    $http({
        method: 'GET',
        url: IPAddress + '/voucherApp/customers'
    }).then(function successCallback(response) {

        $scope.customerList = response.data

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

                $scope.open('sm', transferData.txid, transferData.cid, transferData.name)
                console.log($scope.items.usertype)

            }

            else if ($scope.items.usertype == 'Customer' || 'Company') {

                console.log($scope.items.usertype)

                if ($scope.items.usertype == 'Customer')
                    blockUI.start("Transferring voucher to " + transferData.name + " ...");
                else if ($scope.items.usertype == 'Company')
                    blockUI.start("Transferring voucher to " + transferData.donor + " ...");
                $timeout(function () {
                    blockUI.message('Adding transaction to bigchain...');
                }, 2000);


                $timeout(function () {
                    blockUI.stop();
                }, 1000);

                if ($scope.items.usertype == 'Company') {
                    var trans_to = transferData.donor;
                }
                else if ($scope.items.usertype == 'Customer') {
                    var trans_to = transferData.name;
                }
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
                    url: IPAddress + '/voucherApp/transferVoucher',
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


    $scope.open = function (size, aid, cid, voucherName) {


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
                    return {
                        'data': $scope.items,
                        'assetid': $scope.aid,
                        'cid': $scope.cid,
                        'cList': $scope.customerList,
                        'vname': voucherName
                    }
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
                    return {}
                }
            }

        });

    };

    $scope.toAll = function (size) {


        var modalInstance = $uibModal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'myModalContent2.html',
            controller: 'ModalInstanceCtrl4',
            size: size,
            resolve: {
                items: function () {
                    return {}
                }
            }

        });

    };


    $scope.getBlockDetails = function (blkNumber) {


        console.log(blkNumber)
        console.log("BLK NUMBER---")

        $scope.blockNumber = blkNumber;

        var modalInstance = $uibModal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'myModalContent3.html',
            controller: 'ModalInstanceCtrl3',
            windowClass: 'app-modal-window',
            size: 'lg',
            resolve: {
                items: function () {
                    return {
                        'blkNum': $scope.blockNumber
                    }
                }
            }

        });

    };

});


app.controller('ModalInstanceCtrl', function ($scope, $http, $uibModalInstance, items, $cookies, $window, blockUI, $timeout) {
    $scope.items = items.data;
    $scope.aid = items.assetid;
    $scope.cid = items.cid;
    $scope.customerList = items.cList;

    $scope.selCust = null;
    $scope.vname = items.vname;

    $scope.ok = function () {


        blockUI.start("Transferring voucher to " + $scope.selCust.username + " ...");

        $timeout(function () {
            blockUI.message('Adding transaction to bigchain...');
        }, 2000);


        $timeout(function () {
            blockUI.stop();
        }, 1000);


        console.log($scope.items);
        console.log($scope.aid);
        console.log($scope.cid);
        console.log($scope.selCust);


        var trans_to = $scope.selCust.username;
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
            url: IPAddress + '/voucherApp/transferVoucher',
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


app.controller('ModalInstanceCtrl2', function ($scope, $http, $uibModalInstance, items, $cookies, $window) {

    $scope.ok = function () {

        var trans_from = $cookies.get("user");
        var vname = $scope.nameOfVoucher;
        var vvalue = $scope.valueOfVoucher;

        console.log(trans_from);
        console.log(vname);
        console.log(vvalue);


        $http({
            method: 'POST',
            url: IPAddress + '/voucherApp/createVoucher',
            headers: {'Content-Type': 'application/json'},
            data: {
                username: trans_from,
                voucher_name: vname,
                value: vvalue
            }
        }).success(function (data) {

            console.log(data);

            if (data.status == "error")
                alert(data.errorMessage);
            else {
                $uibModalInstance.close();
                $window.location.reload();
            }

        });

    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});


app.controller('ModalInstanceCtrl3', function ($scope, $http, $uibModalInstance, items) {
    $scope.blockNumber = items.blkNum;


    $http({
        method: 'GET',
        url: IPAddress + '/voucherApp/getBlockContents?blockNumber=' + $scope.blockNumber,
        headers: {'Content-Type': 'application/json'}
    }).then(function successCallback(response) {
        $scope.blockDetails = response.data

        console.log($scope.items)
        console.log("--------")


    }, function errorCallback(response) {
        // called asynchronously if an error occurs
        // or server returns response with an error status.
    });

});

app.controller('ModalInstanceCtrl4', function ($scope, $http, $uibModalInstance, items, $cookies, $window) {

    $scope.ok = function () {

        var trans_from = $cookies.get("user");
        var vname = $scope.nameOfVoucher;
        var vvalue = $scope.valueOfVoucher;

        console.log(trans_from);
        console.log(vname);
        console.log(vvalue);


        $http({
            method: 'POST',
            url: IPAddress + '/voucherApp/createAndTransferVoucher',
            headers: {'Content-Type': 'application/json'},
            data: {
                source_username: trans_from,
                voucher_name: vname,
                value: vvalue
            }
        }).success(function (data) {

            console.log(data);

            if (data.status == "error")
                alert(data.errorMessage);
            else
                $uibModalInstance.close();
            $window.location.reload();

        });

    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };
});






