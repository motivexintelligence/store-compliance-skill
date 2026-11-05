import 'package:flutter/material.dart';

// Fixture for the store-compliance scanner tests. Every line here is a deliberate violation.
const bool isReviewMode = false;

class Home extends StatelessWidget {
  const Home({super.key});
  @override
  Widget build(BuildContext context) {
    if (isReviewMode) return const Text('Coming soon');
    return WillPopScope(onWillPop: () async => false, child: const Text('Lorem ipsum'));
  }
}
