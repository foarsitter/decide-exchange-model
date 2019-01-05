
The format of an input file is as follow 

An row starts with an identifier

| identifier   | meaning  |
|---    |---|
| #0    | Comment, ignored by the program  |
| #/    | Comment, ignored by the program  |
| #A    | Definition of an actor  |
| #P    | Definition of an issue  |
| #M    | Specification of the meaning of different position of an issue  |
| #D    | Definition of an position of an actor on an issue  |

### Actor (#A)
An #A is followed by the key of the actor and an human readable name of the actor

| identifier | key | issue name | comment |
|---|---|---|---|
|#A|LDCs_BGD|Least developed countries| The countries are represented by Bangladesh |
|#A|Brazil|Brazil| some note |

### Issue (#P)
Same as #A the #P is followed by the key of the issue and an human readable name of the issue

| identifier | key | issue name | comment |
|---|---|---|---|
|#P|finance_vol|finance volume| room for thoughts |
|#P|finance_who|finance who pays| room for thoughts |

### Issue Specification (#M)
The key of the issue as defined in the #P row, followed by the position and a description

| identifier   | issue key  | Position | Description |
|---|---|---|---|
|#M|legal|0|No binding agreement or binding country-specific targets|
|#M|legal|30|Binding agreement without country-specific targets. |
|#M|legal|50|Binding agreement plus obligation to have a (nonbinding) country-specific target (NDC)|
|#M|legal|70|The above plus obligation on measuring, reporting and verification.|
|#M|legal|100|Binding agreement plus binding, country-specific targets. |

The program determines the automatically the lower and upper of an issue. When #M is not specified for an issue, the default interval 0-100 is used.


|identifier|actor key|issue key|position|salience|power|
|---|---|---|---|---|---|
|#D|African_grp|differentiation|70|0.75|0.25|
|#D|AILAC|differentiation|50|0.6|0.35|
|#D|ALBA|differentiation|80|0.65|0.05|
|#D|AOSIS|differentiation|40|0.6|0.5|
|#D|Arab_states|differentiation|100|0.75|0.4|
|#D|LDCs_BGD|differentiation|60|0.6|0.5|
|#D|Brazil|differentiation|80|0.8|0.7|
|#D|China|differentiation|80|0.75|1|
|#D|EIG|differentiation|40|0.75|0.35|
|#D|EU28|differentiation|30|0.75|0.75|
|#D|India|differentiation|90|0.75|0.6|
|#D|Umbrella_min|differentiation|25|0.9|0.4|
|#D|Japan|differentiation|25|0.9|0.6|
|#D|Russia|differentiation|15|0.8|0.6|
|#D|USA|differentiation|20|0.95|1|

Important is that the `actor key` and `issue key` are the same as defined by `#A` and `#P` respectively. Otherwise the program will raise an error during loading.

The position has to be on the interval define by `#M` of the specified `issue key`. 

The salience and power are defined on an interval between 0 and 1.   