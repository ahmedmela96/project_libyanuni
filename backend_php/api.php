<?php
// api.php - Basic PHP API for Ehsan (For MySQL/XAMPP)

require_once 'config.php';
header('Content-Type: application/json; charset=utf-8');

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

if ($method === 'POST') {
    $data = json.loads(file_get_contents('php://input'));

    if ($action === 'login') {
        $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ? AND password = ?");
        $stmt->execute([$data['username'], $data['password']]);
        $user = $stmt->fetch();
        if ($user) { echo json_encode($user); } else { http_response_code(401); echo json_encode(["error" => "Invalid credentials"]); }
    }

    if ($action === 'add_beneficiary') {
        // --- Need Score Algorithm ---
        $fs = $data['size'];
        $inc = $data['income'];
        $ct = $data['caseType'];
        
        $fs_score = ($fs <= 2) ? 1 : (($fs <= 5) ? 2 : 3);
        $inc_score = ($inc < 500) ? 3 : (($inc <= 1000) ? 2 : 1);
        $ct_scores = ["orphan" => 3, "patient" => 2, "widow" => 2, "needy" => 1];
        $ct_score = $ct_scores[$ct] ?? 1;
        
        $need_score = (0.4 * $fs_score) + (0.4 * $inc_score) + (0.2 * $ct_score);

        $stmt = $pdo->prepare("INSERT INTO beneficiaries (national_id, name, family_size, case_type, income, need_score, phone) VALUES (?, ?, ?, ?, ?, ?, ?)");
        try {
            $stmt->execute([$data['nationalId'], $data['name'], $fs, $ct, $inc, $need_score, $data['phone']]);
            echo json_encode(["id" => $pdo->lastInsertId(), "needScore" => $need_score]);
        } catch (Exception $e) { http_response_code(400); echo json_encode(["error" => "Duplicate National ID"]); }
    }
}

if ($method === 'GET') {
    if ($action === 'stats') {
        $bCount = $pdo->query("SELECT COUNT(*) FROM beneficiaries")->fetchColumn();
        $dCount = $pdo->query("SELECT COUNT(*) FROM distributions")->fetchColumn();
        echo json_encode(["totalBeneficiaries" => $bCount, "totalDistributions" => $dCount]);
    }
}
?>
