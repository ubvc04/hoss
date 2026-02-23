/*
 * Hospital Management System - Medical Records Chaincode
 * Hyperledger Fabric Smart Contract for data integrity and audit trail
 * 
 * This chaincode stores hashes of medical records for tamper detection.
 * Actual data remains in the traditional database.
 */

package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// MedicalRecordsContract provides functions for managing medical record hashes
type MedicalRecordsContract struct {
	contractapi.Contract
}

// RecordHash represents a hash record stored on the blockchain
type RecordHash struct {
	RecordID    string      `json:"recordId"`
	PatientID   int         `json:"patientId"`
	HashPayload interface{} `json:"hashPayload"` // Can be string or HashPayloadComplex
	RecordType  string      `json:"recordType"`  // PATIENT, VISIT, PRESCRIPTION, REPORT, BILLING, APPOINTMENT
	CreatedBy   int         `json:"createdBy"`
	Timestamp   string      `json:"timestamp"`
	TxID        string      `json:"txId"`
}

// HashPayloadSimple for form-only records
type HashPayloadSimple struct {
	Hash string `json:"hash"`
}

// HashPayloadComplex for reports with files
type HashPayloadComplex struct {
	FormHash string `json:"formHash"`
	FileHash string `json:"fileHash,omitempty"`
	IPFSHash string `json:"ipfsHash,omitempty"`
}

// RecordHistory represents a single history entry
type RecordHistory struct {
	TxID      string      `json:"txId"`
	Timestamp string      `json:"timestamp"`
	Record    *RecordHash `json:"record"`
}

// InitLedger initializes the chaincode (optional setup)
func (c *MedicalRecordsContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	fmt.Println("Medical Records Chaincode initialized")
	return nil
}

// AddRecordHash stores a new record hash on the blockchain
// Parameters:
//   - recordId: Unique identifier (e.g., "PATIENT_123", "VISIT_456")
//   - patientId: The patient this record belongs to
//   - hashPayload: JSON string containing hash data
//   - recordType: Type of record (PATIENT, VISIT, PRESCRIPTION, REPORT, BILLING, APPOINTMENT)
//   - createdBy: User ID who created the record
//   - timestamp: ISO timestamp of creation
func (c *MedicalRecordsContract) AddRecordHash(
	ctx contractapi.TransactionContextInterface,
	recordId string,
	patientId int,
	hashPayload string,
	recordType string,
	createdBy int,
	timestamp string,
) error {
	// Validate record type
	validTypes := map[string]bool{
		"PATIENT":      true,
		"VISIT":        true,
		"PRESCRIPTION": true,
		"REPORT":       true,
		"BILLING":      true,
		"APPOINTMENT":  true,
	}
	if !validTypes[recordType] {
		return fmt.Errorf("invalid record type: %s", recordType)
	}

	// Parse hash payload
	var payload interface{}
	if err := json.Unmarshal([]byte(hashPayload), &payload); err != nil {
		return fmt.Errorf("invalid hash payload JSON: %v", err)
	}

	// Get transaction ID
	txID := ctx.GetStub().GetTxID()

	// Create record
	record := RecordHash{
		RecordID:    recordId,
		PatientID:   patientId,
		HashPayload: payload,
		RecordType:  recordType,
		CreatedBy:   createdBy,
		Timestamp:   timestamp,
		TxID:        txID,
	}

	// Serialize and store
	recordJSON, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("failed to marshal record: %v", err)
	}

	// Use composite key for better querying
	compositeKey, err := ctx.GetStub().CreateCompositeKey("RECORD", []string{recordType, recordId, timestamp})
	if err != nil {
		return fmt.Errorf("failed to create composite key: %v", err)
	}

	// Store with composite key
	err = ctx.GetStub().PutState(compositeKey, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to put state: %v", err)
	}

	// Also store with simple key for direct lookups
	simpleKey := fmt.Sprintf("%s_%s", recordType, recordId)
	err = ctx.GetStub().PutState(simpleKey, recordJSON)
	if err != nil {
		return fmt.Errorf("failed to put state with simple key: %v", err)
	}

	fmt.Printf("Record hash stored: %s (TxID: %s)\n", recordId, txID)
	return nil
}

// GetRecordHash retrieves the latest hash record for a given record ID and type
func (c *MedicalRecordsContract) GetRecordHash(
	ctx contractapi.TransactionContextInterface,
	recordId string,
	recordType string,
) (*RecordHash, error) {
	simpleKey := fmt.Sprintf("%s_%s", recordType, recordId)
	recordJSON, err := ctx.GetStub().GetState(simpleKey)
	if err != nil {
		return nil, fmt.Errorf("failed to read state: %v", err)
	}
	if recordJSON == nil {
		return nil, fmt.Errorf("record not found: %s", simpleKey)
	}

	var record RecordHash
	if err := json.Unmarshal(recordJSON, &record); err != nil {
		return nil, fmt.Errorf("failed to unmarshal record: %v", err)
	}

	return &record, nil
}

// GetRecordHistory retrieves all versions of a record (for audit trail)
func (c *MedicalRecordsContract) GetRecordHistory(
	ctx contractapi.TransactionContextInterface,
	recordId string,
	recordType string,
) ([]*RecordHistory, error) {
	simpleKey := fmt.Sprintf("%s_%s", recordType, recordId)
	historyIterator, err := ctx.GetStub().GetHistoryForKey(simpleKey)
	if err != nil {
		return nil, fmt.Errorf("failed to get history: %v", err)
	}
	defer historyIterator.Close()

	var history []*RecordHistory
	for historyIterator.HasNext() {
		modification, err := historyIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate history: %v", err)
		}

		var record RecordHash
		if err := json.Unmarshal(modification.Value, &record); err != nil {
			continue // Skip invalid entries
		}

		historyEntry := &RecordHistory{
			TxID:      modification.TxId,
			Timestamp: time.Unix(modification.Timestamp.Seconds, int64(modification.Timestamp.Nanos)).Format(time.RFC3339),
			Record:    &record,
		}
		history = append(history, historyEntry)
	}

	return history, nil
}

// GetRecordsByPatient retrieves all records for a specific patient
func (c *MedicalRecordsContract) GetRecordsByPatient(
	ctx contractapi.TransactionContextInterface,
	patientId int,
) ([]*RecordHash, error) {
	// Query all record types for this patient
	queryString := fmt.Sprintf(`{"selector":{"patientId":%d}}`, patientId)
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, fmt.Errorf("failed to execute query: %v", err)
	}
	defer resultsIterator.Close()

	var records []*RecordHash
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var record RecordHash
		if err := json.Unmarshal(queryResponse.Value, &record); err != nil {
			continue
		}
		records = append(records, &record)
	}

	return records, nil
}

// GetRecordsByType retrieves all records of a specific type
func (c *MedicalRecordsContract) GetRecordsByType(
	ctx contractapi.TransactionContextInterface,
	recordType string,
) ([]*RecordHash, error) {
	resultsIterator, err := ctx.GetStub().GetStateByPartialCompositeKey("RECORD", []string{recordType})
	if err != nil {
		return nil, fmt.Errorf("failed to get records by type: %v", err)
	}
	defer resultsIterator.Close()

	var records []*RecordHash
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, fmt.Errorf("failed to iterate results: %v", err)
		}

		var record RecordHash
		if err := json.Unmarshal(queryResponse.Value, &record); err != nil {
			continue
		}
		records = append(records, &record)
	}

	return records, nil
}

// VerifyHash compares a provided hash against the stored hash
func (c *MedicalRecordsContract) VerifyHash(
	ctx contractapi.TransactionContextInterface,
	recordId string,
	recordType string,
	providedHash string,
) (bool, error) {
	record, err := c.GetRecordHash(ctx, recordId, recordType)
	if err != nil {
		return false, err
	}

	// Extract hash from payload
	payloadJSON, err := json.Marshal(record.HashPayload)
	if err != nil {
		return false, fmt.Errorf("failed to marshal hash payload: %v", err)
	}

	// For simple hash
	var simplePayload HashPayloadSimple
	if err := json.Unmarshal(payloadJSON, &simplePayload); err == nil && simplePayload.Hash != "" {
		return simplePayload.Hash == providedHash, nil
	}

	// For complex hash (reports)
	var complexPayload HashPayloadComplex
	if err := json.Unmarshal(payloadJSON, &complexPayload); err == nil {
		return complexPayload.FormHash == providedHash, nil
	}

	return false, fmt.Errorf("unable to parse hash payload")
}

func main() {
	chaincode, err := contractapi.NewChaincode(&MedicalRecordsContract{})
	if err != nil {
		fmt.Printf("Error creating chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting chaincode: %v\n", err)
	}
}
