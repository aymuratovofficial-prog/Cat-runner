<!DOCTYPE html>
<html lang="kaa">
<head>
    <meta charset="UTF-8">
    <title>Natiyje</title>
</head>
<body>
    <?php
    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        // Formadan kelgen sandı alamız
        $a = $_POST['san'];
        
        // Kvadratın esaplaymız: a * a
        $kvadrat = $a * $a;
        
        echo "<h3>Kiritilgen san: $a</h3>";
        echo "<h2>Esaplaw natiyjesi: $a<sup>2</sup> = $kvadrat</h2>";
        
        echo '<br><a href="index.html">Arqaǵa qaytıw</a>';
    } else {
        echo "<p>Aldın formanı toltırıń!</p>";
    }
    ?>
</body>
</html>
